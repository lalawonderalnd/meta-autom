"""Per-device health checks."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from accfarm_device.device import Device

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """Health status of a device."""

    device_serial: str
    is_online: bool
    battery_level: int | None
    battery_charging: bool
    screen_on: bool
    storage_free_mb: float | None
    memory_free_mb: float | None
    temperature_c: float | None
    foreground_app: str | None
    atx_agent_running: bool
    last_check: datetime


class HealthChecker:
    """Per-device health check service."""

    def __init__(self):
        self._last_status: dict[str, HealthStatus] = {}

    def check(self, device: "Device") -> HealthStatus:
        """
        Perform comprehensive health check on a device.

        Args:
            device: Target device

        Returns:
            HealthStatus with all metrics
        """
        now = datetime.now(timezone.utc)

        # Basic connectivity
        is_online = device.is_online()

        # Initialize defaults
        battery_level = None
        battery_charging = False
        screen_on = False
        storage_free_mb = None
        memory_free_mb = None
        temperature_c = None
        foreground_app = None
        atx_agent_running = False

        if is_online and device._adb_client:
            serial = device.serial

            try:
                # Battery info
                battery_output = device._adb_client.shell(
                    serial,
                    "dumpsys battery",
                    timeout=10,
                )
                for line in battery_output.splitlines():
                    if "level:" in line:
                        try:
                            battery_level = int(line.split(":")[1].strip())
                        except (ValueError, IndexError):
                            pass
                    if "AC powered:" in line or "USB powered:" in line or "Wireless powered:" in line:
                        battery_charging = "true" in line.lower()
                    if "temperature:" in line:
                        try:
                            # Temperature is usually in tenths of degrees
                            temp = int(line.split(":")[1].strip())
                            temperature_c = temp / 10.0
                        except (ValueError, IndexError):
                            pass

                # Screen state
                power_output = device._adb_client.shell(
                    serial,
                    "dumpsys power | grep mWakefulness",
                    timeout=10,
                )
                screen_on = "Asleep" not in power_output and "Dozing" not in power_output

                # Storage info
                storage_output = device._adb_client.shell(
                    serial,
                    "df /data",
                    timeout=10,
                )
                # Parse df output - look for Available column
                lines = storage_output.strip().splitlines()
                if len(lines) >= 2:
                    parts = lines[-1].split()
                    if len(parts) >= 4:
                        # Available is typically in KB
                        available_kb = int(parts[3])
                        storage_free_mb = available_kb / 1024

                # Memory info
                mem_output = device._adb_client.shell(
                    serial,
                    "cat /proc/meminfo | grep MemAvailable",
                    timeout=10,
                )
                if mem_output:
                    try:
                        # MemAvailable is in kB
                        available_kb = int(mem_output.split()[1])
                        memory_free_mb = available_kb / 1024
                    except (ValueError, IndexError):
                        pass

                # Foreground app
                fg_output = device._adb_client.shell(
                    serial,
                    "dumpsys window | grep mCurrentFocus",
                    timeout=10,
                )
                if "/" in fg_output:
                    foreground_app = fg_output.split("/")[-1].split(" ")[0]

                # Check ATX agent
                atx_output = device._adb_client.shell(
                    serial,
                    "ps | grep atx-agent",
                    timeout=10,
                )
                atx_agent_running = "atx-agent" in atx_output

            except Exception as e:
                logger.warning(
                    "Health check partial failure",
                    extra={"serial": serial, "error": str(e)},
                )

        status = HealthStatus(
            device_serial=device.serial,
            is_online=is_online,
            battery_level=battery_level,
            battery_charging=battery_charging,
            screen_on=screen_on,
            storage_free_mb=storage_free_mb,
            memory_free_mb=memory_free_mb,
            temperature_c=temperature_c,
            foreground_app=foreground_app,
            atx_agent_running=atx_agent_running,
            last_check=now,
        )

        self._last_status[device.serial] = status
        return status

    def is_healthy(
        self,
        device: "Device",
        *,
        min_battery: int = 20,
        min_storage_mb: float = 500,
        max_temperature: float = 45.0,
    ) -> bool:
        """
        Check if a device is healthy enough for operation.

        Args:
            device: Target device
            min_battery: Minimum battery percentage
            min_storage_mb: Minimum free storage in MB
            max_temperature: Maximum temperature in Celsius

        Returns:
            True if device is healthy
        """
        status = self.check(device)

        if not status.is_online:
            logger.warning("Device offline", extra={"serial": device.serial})
            return False

        if status.battery_level is not None and status.battery_level < min_battery:
            logger.warning(
                "Low battery",
                extra={"serial": device.serial, "battery": status.battery_level},
            )
            return False

        if status.storage_free_mb is not None and status.storage_free_mb < min_storage_mb:
            logger.warning(
                "Low storage",
                extra={"serial": device.serial, "free_mb": status.storage_free_mb},
            )
            return False

        if status.temperature_c is not None and status.temperature_c > max_temperature:
            logger.warning(
                "High temperature",
                extra={"serial": device.serial, "temp_c": status.temperature_c},
            )
            return False

        if not status.atx_agent_running:
            logger.warning("ATX agent not running", extra={"serial": device.serial})
            return False

        return True

    def get_last_status(self, serial: str) -> HealthStatus | None:
        """Get the last recorded health status for a device."""
        return self._last_status.get(serial)

    def get_all_statuses(self) -> dict[str, HealthStatus]:
        """Get health status for all checked devices."""
        return self._last_status.copy()
