"""ADB client wrapper with retry/reconnect logic."""

from __future__ import annotations

import logging
from functools import wraps
from typing import Callable, TypeVar

import adbutils
from tenacity import retry, stop_after_attempt, wait_exponential

from accfarm_device.exceptions import DeviceOfflineError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def adb_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator for ADB operations with exponential backoff."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    # Apply tenacity retry to the inner function
    retry_func = retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=0.5, max=4),
        reraise=True,
    )(func)

    return wrapper


class AdbClient:
    """Wrapper around adbutils with retry/reconnect logic and connection pooling."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5037):
        self._host = host
        self._port = port
        self._adb = adbutils.AdbClient(host=host, port=port)
        self._connections: dict[str, tuple[str, int]] = {}  # serial -> (ip, port)

    def connect(self, serial: str, ip: str, port: int = 5555) -> bool:
        """Connect to a device via Wi-Fi ADB. Returns True if successful."""
        try:
            self._adb.connect(f"{ip}:{port}", timeout=10)
            self._connections[serial] = (ip, port)
            logger.info("Connected to device via Wi-Fi ADB", extra={"serial": serial, "ip": ip, "port": port})
            return True
        except adbutils.AdbError as e:
            logger.error("Failed to connect to device", extra={"serial": serial, "ip": ip, "error": str(e)})
            return False

    def disconnect(self, serial: str) -> None:
        """Disconnect from a device."""
        if serial in self._connections:
            ip, port = self._connections[serial]
            try:
                self._adb.disconnect(f"{ip}:{port}")
            except adbutils.AdbError:
                pass
            del self._connections[serial]
            logger.info("Disconnected from device", extra={"serial": serial})

    @adb_retry
    def shell(self, serial: str, command: str, timeout: int = 30) -> str:
        """Run a shell command on the device with retry logic."""
        try:
            device = self._adb.device(serial=serial)
            output = device.shell(command, timeout=timeout)
            return output.strip() if output else ""
        except adbutils.AdbError as e:
            logger.warning("ADB shell failed", extra={"serial": serial, "command": command, "error": str(e)})
            raise DeviceOfflineError(f"Device {serial} unreachable: {e}")

    @adb_retry
    def list_devices(self) -> list[adbutils.AdbDevice]:
        """List all connected devices."""
        return self._adb.list()

    def get_device(self, serial: str) -> adbutils.AdbDevice:
        """Get an AdbDevice instance for a serial."""
        return self._adb.device(serial=serial)

    def check_connection(self, serial: str) -> bool:
        """Check if a device is reachable."""
        try:
            result = self.shell(serial, "echo ok", timeout=5)
            return result == "ok"
        except DeviceOfflineError:
            return False

    def reconnect(self, serial: str) -> bool:
        """Reconnect to a device via Wi-Fi ADB."""
        if serial not in self._connections:
            logger.warning("Cannot reconnect: no connection info", extra={"serial": serial})
            return False

        ip, port = self._connections[serial]
        try:
            self._adb.disconnect(f"{ip}:{port}")
        except adbutils.AdbError:
            pass

        return self.connect(serial, ip, port)
