"""Clone representation - one App Cloner clone of Instagram."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accfarm_device.device import Device

logger = logging.getLogger(__name__)


@dataclass
class Clone:
    """Represents one App Cloner clone of Instagram."""

    package_name: str  # e.g. com.instagram.androidp7
    label: str | None = None  # As shown in launcher
    version_name: str | None = None  # IG version
    launch_activity: str | None = None
    _device: "Device | None" = field(default=None, repr=False)

    def __post_init__(self):
        if self._device is not None and self.label is None:
            self.refresh_info(self._device)

    def set_device(self, device: "Device") -> None:
        """Set the device this clone belongs to."""
        self._device = device

    def refresh_info(self, device: "Device") -> None:
        """Refresh clone information from the device."""
        if device._adb_client is None:
            return

        try:
            # Get package info
            output = device._adb_client.shell(
                device.serial,
                f"dumpsys package {self.package_name} | grep -E 'versionName|label'",
                timeout=10,
            )
            for line in output.splitlines():
                if "versionName=" in line:
                    self.version_name = line.split("=")[1].strip()
                elif "label=" in line:
                    self.label = line.split("=")[1].strip()

            # Detect launch activity dynamically
            self.launch_activity = self._detect_launch_activity(device)
        except Exception as e:
            logger.warning("Failed to refresh clone info", extra={"package": self.package_name, "error": str(e)})

    def _detect_launch_activity(self, device: "Device") -> str | None:
        """Detect the launch activity for this clone."""
        if device._adb_client is None:
            return None

        try:
            output = device._adb_client.shell(
                device.serial,
                f"dumpsys package {self.package_name} | grep -A 2 'android.intent.action.MAIN'",
                timeout=10,
            )
            # Look for the activity in lines following MAIN action
            # Format can be:
            #   android.intent.action.MAIN:
            #     1234567 com.package.ActivityName filter abcdefg
            lines = output.splitlines()
            for i, line in enumerate(lines):
                if "android.intent.action.MAIN" in line:
                    # Check subsequent lines for activity
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j]
                        # Look for pattern: hash package.ActivityName filter
                        parts = next_line.strip().split()
                        for part in parts:
                            if "/" in part and self.package_name in part:
                                # Found full activity name like com.package.Activity
                                return part
                            elif "/" in part and part.count("/") == 1:
                                # Found relative activity name like .ActivityName
                                return f"{self.package_name}{part}"
        except Exception as e:
            logger.warning("Failed to detect launch activity", extra={"package": self.package_name, "error": str(e)})

        # Fallback to default Instagram activity
        return f"{self.package_name}.activity.MainTabActivity"

    def launch(self, device: "Device") -> None:
        """Launch this clone."""
        if device._adb_client is None:
            raise RuntimeError("ADB client not set")

        if self.launch_activity is None:
            self.refresh_info(device)

        activity = self.launch_activity or f"{self.package_name}.activity.MainTabActivity"

        logger.info("Launching clone", extra={"serial": device.serial, "package": self.package_name})
        device._adb_client.shell(
            device.serial,
            f"am start -n {activity}",
            timeout=10,
        )

    def force_close(self, device: "Device") -> None:
        """Force-close this clone."""
        if device._adb_client is None:
            raise RuntimeError("ADB client not set")

        logger.debug("Force-closing clone", extra={"serial": device.serial, "package": self.package_name})
        device._adb_client.shell(
            device.serial,
            f"am force-stop {self.package_name}",
            timeout=10,
        )

    def is_foreground(self, device: "Device") -> bool:
        """Check if this clone is currently in the foreground."""
        if device._adb_client is None:
            return False

        try:
            # Primary method: dumpsys window mCurrentFocus
            output = device._adb_client.shell(
                device.serial,
                "dumpsys window | grep mCurrentFocus",
                timeout=10,
            )
            if self.package_name in output:
                return True

            # Fallback: dumpsys activity activities
            output = device._adb_client.shell(
                device.serial,
                "dumpsys activity activities | grep mResumedActivity",
                timeout=10,
            )
            return self.package_name in output
        except Exception as e:
            logger.warning("Failed to check foreground status", extra={"package": self.package_name, "error": str(e)})
            return False

    def clear_data(self, device: "Device") -> None:
        """Clear all data for this clone. USE WITH EXTREME CAUTION — wipes login."""
        if device._adb_client is None:
            raise RuntimeError("ADB client not set")

        logger.warning("Clearing clone data", extra={"serial": device.serial, "package": self.package_name})
        device._adb_client.shell(
            device.serial,
            f"pm clear {self.package_name}",
            timeout=10,
        )
