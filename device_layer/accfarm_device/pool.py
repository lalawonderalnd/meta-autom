"""Device pool - the public entry point for device management."""

from __future__ import annotations

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator
from uuid import UUID, uuid4

import uiautomator2 as u2

from accfarm_device.adb_client import AdbClient
from accfarm_device.clone import Clone
from accfarm_device.device import Device, DeviceStatus
from accfarm_device.exceptions import (
    CloneNotFoundError,
    DeviceMutexTimeoutError,
    DeviceOfflineError,
)
from accfarm_device.u2_session import U2Session

logger = logging.getLogger(__name__)


class DevicePool:
    """
    Singleton-ish device pool. Tracks every known phone, maintains ADB
    connections, hands out U2Sessions with a per-phone mutex.
    """

    def __init__(self, adb_host: str = "127.0.0.1", adb_port: int = 5037):
        self._adb_client = AdbClient(host=adb_host, port=adb_port)
        self._devices: dict[UUID, Device] = {}
        self._device_locks: dict[UUID, threading.Lock] = {}
        self._serial_to_id: dict[str, UUID] = {}

        # Start heartbeat thread
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        self._running = True

    def _heartbeat_loop(self) -> None:
        """Background thread that checks device health every 60 seconds."""
        while self._running:
            time.sleep(60)
            for device in list(self._devices.values()):
                try:
                    if not device.is_online():
                        logger.warning("Device offline", extra={"serial": device.serial})
                        device.status = DeviceStatus.OFFLINE
                        # Try to reconnect
                        if device.ip:
                            device.reconnect()
                except Exception as e:
                    logger.error("Heartbeat error", extra={"serial": device.serial, "error": str(e)})

    def register_device(
        self,
        serial: str,
        ip: str | None = None,
        port: int = 5555,
        name: str | None = None,
    ) -> Device:
        """Add a phone to the pool. Persists to DB. Connects via Wi-Fi ADB if ip given."""
        device_id = uuid4()

        device = Device(
            id=device_id,
            serial=serial,
            name=name or serial,
            ip=ip,
            adb_port=port,
            status=DeviceStatus.IDLE,
        )
        device.set_adb_client(self._adb_client)

        # Connect via Wi-Fi ADB if IP provided
        if ip:
            if not self._adb_client.connect(serial, ip, port):
                raise DeviceOfflineError(f"Failed to connect to {ip}:{port}")
            device.refresh_info()

        self._devices[device_id] = device
        self._serial_to_id[serial] = device_id
        self._device_locks[device_id] = threading.Lock()

        logger.info("Registered device", extra={"device_id": device_id, "serial": serial, "ip": ip})
        return device

    def unregister_device(self, serial: str) -> None:
        """Remove a device from the pool."""
        if serial not in self._serial_to_id:
            return

        device_id = self._serial_to_id[serial]
        device = self._devices.pop(device_id, None)

        if device and device.ip:
            self._adb_client.disconnect(serial)

        self._device_locks.pop(device_id, None)
        self._serial_to_id.pop(serial, None)

        logger.info("Unregistered device", extra={"serial": serial})

    def list_devices(self) -> list[Device]:
        """Return all known devices with their current online status."""
        for device in self._devices.values():
            if device.status != DeviceStatus.BUSY:
                device.status = DeviceStatus.ONLINE if device.is_online() else DeviceStatus.OFFLINE
        return list(self._devices.values())

    def get_device(self, device_id: UUID) -> Device:
        """Get a device by ID."""
        if device_id not in self._devices:
            raise KeyError(f"Device {device_id} not found")
        return self._devices[device_id]

    def get_device_by_serial(self, serial: str) -> Device | None:
        """Get a device by serial."""
        device_id = self._serial_to_id.get(serial)
        if device_id is None:
            return None
        return self._devices.get(device_id)

    @contextmanager
    def acquire(
        self,
        device_id: UUID,
        clone_package: str,
        timeout_seconds: int = 60,
        account_id: UUID | None = None,
    ) -> Iterator[U2Session]:
        """
        Context manager that:
          1. Acquires the per-phone mutex (blocks if another job is using this phone).
          2. Verifies the device is online; reconnects if needed.
          3. Force-closes any other Instagram clone currently in foreground.
          4. Launches the requested clone with its proxy injected.
          5. Yields a U2Session bound to that clone.
          6. On exit: closes the IG clone gracefully, releases the mutex.
        """
        if device_id not in self._devices:
            raise KeyError(f"Device {device_id} not found")

        device = self._devices[device_id]
        lock = self._device_locks.get(device_id)

        if lock is None:
            raise RuntimeError(f"No lock for device {device_id}")

        # Acquire mutex with timeout
        acquired = lock.acquire(timeout=timeout_seconds)
        if not acquired:
            raise DeviceMutexTimeoutError(f"Could not acquire lock for device {device_id} within {timeout_seconds}s")

        try:
            # Verify device is online
            if not device.is_online():
                if device.ip:
                    if not device.reconnect():
                        raise DeviceOfflineError(f"Device {device.serial} unreachable")
                else:
                    raise DeviceOfflineError(f"Device {device.serial} has no IP configured")

            device.status = DeviceStatus.BUSY

            # Find the clone
            clones = device.list_clones()
            clone = next((c for c in clones if c.package_name == clone_package), None)
            if clone is None:
                raise CloneNotFoundError(f"Clone {clone_package} not found on device {device.serial}")

            # Force-close all other Instagram clones
            for other_clone in clones:
                if other_clone.package_name != clone_package:
                    other_clone.force_close(device)

            # Ensure screen is on and unlocked
            self._ensure_screen_on(device)

            # Launch the clone
            clone.launch(device)
            time.sleep(2)  # Wait for app to start

            # Connect uiautomator2
            if device.ip is None:
                raise DeviceOfflineError(f"Device {device.serial} has no IP")

            u2_device = u2.connect(f"{device.ip}:{device.adb_port}")

            # Verify clone is foreground
            if not clone.is_foreground(device):
                logger.warning("Clone not in foreground after launch", extra={"package": clone_package})

            # Create session
            session_account_id = account_id or uuid4()
            session = U2Session(u2_device, clone, device, session_account_id)

            logger.info(
                "Acquired session",
                extra={
                    "device_id": device_id,
                    "clone": clone_package,
                    "account_id": session_account_id,
                },
            )

            yield session

        finally:
            # Cleanup: force-close the clone
            try:
                if clone := next((c for c in device.list_clones() if c.package_name == clone_package), None):
                    clone.force_close(device)
            except Exception as e:
                logger.warning("Failed to force-close clone on release", extra={"error": str(e)})

            device.status = DeviceStatus.IDLE
            lock.release()

    def _ensure_screen_on(self, device: Device) -> None:
        """Ensure the device screen is on and unlocked."""
        if device._adb_client is None:
            return

        # Turn screen on
        device._adb_client.shell(device.serial, "input keyevent 224", timeout=5)  # KEYCODE_WAKEUP

        # Swipe to unlock (simple swipe up from bottom)
        device._adb_client.shell(
            device.serial,
            "input swipe 500 1800 500 500",
            timeout=5,
        )
        time.sleep(1)

    def killswitch(self, device_id: UUID) -> None:
        """Emergency stop: force-close all clones, drop ADB connection, mark device IDLE."""
        if device_id not in self._devices:
            return

        device = self._devices[device_id]
        lock = self._device_locks.get(device_id)

        logger.warning("Killswitch activated", extra={"device_id": device_id, "serial": device.serial})

        # Force-close all Instagram clones
        try:
            device.force_close_all_instagram()
        except Exception as e:
            logger.error("Failed to force-close clones during killswitch", extra={"error": str(e)})

        # Disconnect ADB
        if device.ip:
            try:
                self._adb_client.disconnect(device.serial)
            except Exception:
                pass

        # Mark as idle
        device.status = DeviceStatus.IDLE

        # Release lock if held
        if lock and lock.locked():
            try:
                lock.release()
            except RuntimeError:
                pass  # Lock was not held by current thread

    def shutdown(self) -> None:
        """Shutdown the pool and stop background threads."""
        self._running = False
        for device in self._devices.values():
            if device.ip:
                try:
                    self._adb_client.disconnect(device.serial)
                except Exception:
                    pass
        self._devices.clear()
        self._device_locks.clear()
        self._serial_to_id.clear()
