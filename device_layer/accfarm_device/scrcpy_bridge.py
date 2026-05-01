"""WebSocket bridge to ws-scrcpy for dashboard live view."""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accfarm_device.device import Device

logger = logging.getLogger(__name__)


class ScrcpyBridge:
    """Bridge to ws-scrcpy for WebSocket-based screen streaming."""

    def __init__(self, ws_scrcpy_base: str = "http://localhost:8001"):
        """
        Initialize scrcpy bridge.

        Args:
            ws_scrcpy_base: Base URL of ws-scrcpy server
        """
        self._base_url = ws_scrcpy_base.rstrip("/")
        self._running_processes: dict[str, subprocess.Popen] = {}

    def get_stream_url(self, device: "Device") -> str:
        """
        Get the WebSocket stream URL for a device.

        Args:
            device: Target device

        Returns:
            Full URL for iframe embedding
        """
        if not device.serial:
            raise ValueError("Device has no serial")

        # ws-scrcpy URL format: http://localhost:8001/?action=stream&udid={serial}&player=mse
        return f"{self._base_url}/?action=stream&udid={device.serial}&player=mse"

    def start_for_device(self, device: "Device") -> None:
        """
        Ensure ws-scrcpy is streaming for this device. Idempotent.

        Args:
            device: Target device
        """
        if not device.serial:
            raise ValueError("Device has no serial")

        # Check if already running
        if device.serial in self._running_processes:
            if self._running_processes[device.serial].poll() is None:
                logger.debug(
                    "ws-scrcpy already running for device",
                    extra={"serial": device.serial},
                )
                return

        # ws-scrcpy typically runs as a separate Node process and auto-discovers devices.
        # We just need to ensure it's running; we don't start it ourselves.
        # This method is here for potential future integration where we might
        # spawn ws-scrcpy per-device or manage its lifecycle.

        logger.info(
            "ws-scrcpy stream ready for device",
            extra={"serial": device.serial, "url": self.get_stream_url(device)},
        )

    def stop_for_device(self, device: "Device") -> None:
        """
        Stop ws-scrcpy stream for a device.

        Args:
            device: Target device
        """
        if device.serial in self._running_processes:
            proc = self._running_processes.pop(device.serial)
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

        logger.debug(
            "ws-scrcpy stream stopped for device",
            extra={"serial": device.serial},
        )

    def is_streaming(self, device: "Device") -> bool:
        """
        Check if ws-scrcpy is currently streaming for a device.

        Args:
            device: Target device

        Returns:
            True if streaming
        """
        if not device.serial:
            return False

        if device.serial in self._running_processes:
            return self._running_processes[device.serial].poll() is None

        # In typical deployment, ws-scrcpy runs independently and handles
        # all connected devices. We assume it's available.
        return True

    @classmethod
    def check_ws_scrcpy_available(cls, base_url: str = "http://localhost:8001") -> bool:
        """
        Check if ws-scrcpy server is reachable.

        Args:
            base_url: ws-scrcpy server URL

        Returns:
            True if reachable
        """
        import httpx

        try:
            response = httpx.get(base_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def shutdown(self) -> None:
        """Shutdown all running ws-scrcpy processes."""
        for serial, proc in list(self._running_processes.items()):
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()

        self._running_processes.clear()
        logger.info("All ws-scrcpy streams stopped")
