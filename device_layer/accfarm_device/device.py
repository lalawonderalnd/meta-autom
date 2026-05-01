"""Device representation - one physical Android phone."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from accfarm_device.adb_client import AdbClient
    from accfarm_device.clone import Clone

logger = logging.getLogger(__name__)


class DeviceStatus(str, Enum):
    """Device status enumeration."""

    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"


@dataclass
class Device:
    """Represents one physical Android phone in the farm."""

    id: UUID
    serial: str
    name: str
    ip: str | None
    adb_port: int
    android_version: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    status: DeviceStatus = DeviceStatus.IDLE
    last_heartbeat: datetime | None = None
    _adb_client: "AdbClient | None" = field(default=None, repr=False)

    def is_online(self) -> bool:
        """Check if device is reachable via ADB."""
        if self._adb_client is None:
            return False
        return self._adb_client.check_connection(self.serial)

    def reconnect(self) -> bool:
        """Re-establish Wi-Fi ADB connection. Returns True if successful."""
        if self._adb_client is None or self.ip is None:
            return False
        logger.info("Reconnecting to device", extra={"serial": self.serial, "ip": self.ip})
        return self._adb_client.reconnect(self.serial)

    def set_adb_client(self, client: "AdbClient") -> None:
        """Set the ADB client for this device."""
        self._adb_client = client

    def list_clones(self) -> list["Clone"]:
        """List all Instagram clones on this device."""
        from accfarm_device.clone import Clone

        if self._adb_client is None:
            raise RuntimeError("ADB client not set")

        try:
            output = self._adb_client.shell(self.serial, "pm list packages | grep instagram")
        except Exception as e:
            logger.warning("Failed to list packages", extra={"serial": self.serial, "error": str(e)})
            return []

        clones = []
        for line in output.splitlines():
            pkg = line.replace("package:", "").strip()
            if pkg:
                clone = Clone(package_name=pkg, device=self)
                clone.refresh_info(self)
                clones.append(clone)

        return clones

    def force_close_all_instagram(self) -> None:
        """Force-stop all Instagram clone packages."""
        if self._adb_client is None:
            raise RuntimeError("ADB client not set")

        clones = self.list_clones()
        for clone in clones:
            clone.force_close(self)
            logger.info("Force-closed clone", extra={"serial": self.serial, "package": clone.package_name})

    def install_atx_agent(self) -> None:
        """Install uiautomator2 ATX agent on the device."""
        import uiautomator2 as u2

        if self.ip is None:
            raise RuntimeError("Cannot install ATX agent without IP address")

        logger.info("Installing ATX agent", extra={"serial": self.serial, "ip": self.ip})
        try:
            u2.connect(f"{self.ip}:{self.adb_port}")
            logger.info("ATX agent installed successfully", extra={"serial": self.serial})
        except Exception as e:
            logger.error("Failed to install ATX agent", extra={"serial": self.serial, "error": str(e)})
            raise

    def heartbeat(self) -> dict:
        """Return basic device stats."""
        if self._adb_client is None:
            return {}

        try:
            # Battery info
            battery_output = self._adb_client.shell(
                self.serial,
                "dumpsys battery | grep -E 'level|temperature'",
                timeout=10,
            )
            battery_level = None
            for line in battery_output.splitlines():
                if "level:" in line:
                    try:
                        battery_level = int(line.split(":")[1].strip())
                    except (ValueError, IndexError):
                        pass

            # Screen state
            screen_output = self._adb_client.shell(
                self.serial,
                "dumpsys power | grep mWakefulness",
                timeout=10,
            )
            screen_on = "Asleep" not in screen_output and "Dozing" not in screen_output

            # Foreground app
            fg_output = self._adb_client.shell(
                self.serial,
                "dumpsys window | grep mCurrentFocus",
                timeout=10,
            )
            foreground_app = fg_output.split("/")[-1].split(" ")[0] if "/" in fg_output else None

            return {
                "battery_level": battery_level,
                "screen_on": screen_on,
                "foreground_app": foreground_app,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning("Heartbeat failed", extra={"serial": self.serial, "error": str(e)})
            return {"error": str(e)}

    def get_property(self, prop: str) -> str | None:
        """Get a system property from the device."""
        if self._adb_client is None:
            return None
        try:
            return self._adb_client.shell(self.serial, f"getprop {prop}")
        except Exception:
            return None

    def refresh_info(self) -> None:
        """Refresh device information (manufacturer, model, Android version)."""
        if self._adb_client is None:
            return

        self.manufacturer = self.get_property("ro.product.manufacturer")
        self.model = self.get_property("ro.product.model")
        self.android_version = self.get_property("ro.build.version.release")
        self.last_heartbeat = datetime.now(timezone.utc)
