"""Screenshot and screen recording utilities."""

from __future__ import annotations

import io
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accfarm_device.device import Device

logger = logging.getLogger(__name__)


class ScreenService:
    """Screenshot and screen recording service."""

    def __init__(self, device: "Device", use_scrcpy: bool = False):
        self._device = device
        self._use_scrcpy = use_scrcpy

    def screenshot(self) -> bytes:
        """
        Take a screenshot and return PNG bytes.

        Uses uiautomator2's screenshot by default, falls back to scrcpy
        if enabled and uiautomator2 fails.
        """
        import uiautomator2 as u2

        if self._device.ip is None:
            raise RuntimeError("Cannot screenshot without IP")

        try:
            # Try uiautomator2 first
            u2_device = u2.connect(f"{self._device.ip}:{self._device.adb_port}")
            img = u2_device.screenshot()

            # Convert to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        except Exception as e:
            logger.warning(
                "uiautomator2 screenshot failed, trying scrcpy",
                extra={"serial": self._device.serial, "error": str(e)},
            )

            if self._use_scrcpy:
                return self._screenshot_scrcpy()

            raise

    def _screenshot_scrcpy(self) -> bytes:
        """Take screenshot using scrcpy CLI."""
        if self._device.serial is None:
            raise RuntimeError("Cannot screenshot without serial")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Use scrcpy's screenshot feature
            result = subprocess.run(
                [
                    "scrcpy",
                    "--serial",
                    self._device.serial,
                    "--no-control",
                    "--no-display",
                    "--no-audio",
                    "--tunnel-host",
                    "localhost",
                ],
                capture_output=True,
                timeout=10,
            )

            # scrcpy doesn't have direct screenshot CLI, fallback to adb
            if self._device._adb_client:
                self._device._adb_client.shell(
                    self._device.serial,
                    f"screencap -p > /sdcard/screenshot_{self._device.serial}.png",
                    timeout=10,
                )
                # Pull the file
                # Note: adbutils doesn't have pull, would need subprocess adb
                subprocess.run(
                    ["adb", "-s", self._device.serial, "pull", f"/sdcard/screenshot_{self._device.serial}.png", tmp_path],
                    capture_output=True,
                    timeout=10,
                )

                with open(tmp_path, "rb") as f:
                    return f.read()

            raise RuntimeError("scrcpy screenshot not available")

        finally:
            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)

    def start_recording(self, output_path: str | Path, max_duration_sec: int = 300) -> None:
        """
        Start screen recording.

        Args:
            output_path: Where to save the recording
            max_duration_sec: Maximum recording duration
        """
        if self._device._adb_client is None:
            raise RuntimeError("ADB client not set")

        output_path = Path(output_path)

        # Use Android's built-in screenrecord
        remote_path = f"/sdcard/recording_{self._device.serial}.mp4"

        logger.info(
            "Starting screen recording",
            extra={"serial": self._device.serial, "path": str(output_path)},
        )

        # Start recording in background
        self._device._adb_client.shell(
            self._device.serial,
            f"screenrecord --time-limit {max_duration_sec} {remote_path}",
            timeout=max_duration_sec + 10,
        )

    def stop_recording(self, output_path: str | Path) -> bytes:
        """
        Stop recording and return video bytes.

        Args:
            output_path: Local path to save the recording

        Returns:
            Video file bytes
        """
        if self._device._adb_client is None:
            raise RuntimeError("ADB client not set")

        remote_path = f"/sdcard/recording_{self._device.serial}.mp4"
        output_path = Path(output_path)

        # Pull the recording
        logger.info(
            "Stopping screen recording",
            extra={"serial": self._device.serial, "path": str(output_path)},
        )

        subprocess.run(
            ["adb", "-s", self._device.serial, "pull", remote_path, str(output_path)],
            capture_output=True,
            timeout=60,
        )

        # Clean up remote file
        self._device._adb_client.shell(
            self._device.serial,
            f"rm {remote_path}",
            timeout=5,
        )

        with open(output_path, "rb") as f:
            return f.read()

    def get_screen_size(self) -> tuple[int, int]:
        """Get screen dimensions (width, height)."""
        if self._device._adb_client is None:
            return (1080, 1920)  # Default fallback

        try:
            output = self._device._adb_client.shell(
                self._device.serial,
                "wm size",
                timeout=5,
            )
            # Parse "Physical size: 1080x1920"
            for line in output.splitlines():
                if "size:" in line:
                    parts = line.split(":")[1].strip().split("x")
                    return (int(parts[0]), int(parts[1]))
        except Exception as e:
            logger.warning("Failed to get screen size", extra={"error": str(e)})

        return (1080, 1920)
