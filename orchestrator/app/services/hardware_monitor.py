"""
Hardware Monitor - Battery and thermal monitoring for device protection.

Monitors phone battery temperature, voltage, and health to prevent
hardware damage from continuous operation. Auto-throttles when thresholds
are exceeded.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from supabase import Client


class ThermalStatus(str, Enum):
    """Thermal status of a device."""
    NORMAL = "normal"
    WARM = "warm"
    HOT = "hot"
    CRITICAL = "critical"


class BatteryStatus(str, Enum):
    """Battery charging status."""
    CHARGING = "charging"
    DISCHARGING = "discharging"
    FULL = "full"
    NOT_CHARGING = "not_charging"


class HardwareMonitor:
    """
    Hardware health monitoring for Android devices.
    
    Features:
    - Battery temperature monitoring
    - Voltage and current tracking
    - Thermal throttling recommendations
    - Charge cycle counting
    - Automatic device pause on overheating
    """
    
    # Temperature thresholds (°C)
    TEMP_NORMAL_MAX = 35
    TEMP_WARM_MAX = 40
    TEMP_HOT_MAX = 45
    TEMP_CRITICAL = 50
    
    # Battery thresholds
    BATTERY_FULL = 100
    BATTERY_HIGH = 80
    BATTERY_LOW = 20
    BATTERY_CRITICAL = 10
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.device_readings: dict[str, list[dict]] = {}
        self.throttle_recommendations: dict[str, dict] = {}
        
    async def get_battery_info(self, device_serial: str) -> dict:
        """
        Get battery information from device via ADB.
        
        Args:
            device_serial: ADB device serial
            
        Returns:
            Battery status dict
        """
        # In real implementation, this would execute ADB commands:
        # adb -s {serial} shell dumpsys battery
        
        # Simulated response structure
        return {
            "device_serial": device_serial,
            "level": 85,  # Percentage
            "status": BatteryStatus.CHARGING.value,
            "health": "good",
            "present": True,
            "scale": 100,
            "voltage": 4200,  # mV
            "temperature": 38,  # °C (tenths of degree, so 380 = 38.0°C)
            "technology": "Li-ion",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def get_thermal_status(self, device_serial: str) -> dict:
        """
        Get thermal status from device.
        
        Args:
            device_serial: ADB device serial
            
        Returns:
            Thermal status dict with all sensor readings
        """
        # In real implementation:
        # adb -s {serial} shell cat /sys/class/thermal/thermal_zone*/temp
        
        battery_info = await self.get_battery_info(device_serial)
        temp_celsius = battery_info.get("temperature", 35) / 10.0
        
        # Determine thermal status
        if temp_celsius >= self.TEMP_CRITICAL:
            status = ThermalStatus.CRITICAL
        elif temp_celsius >= self.TEMP_HOT:
            status = ThermalStatus.HOT
        elif temp_celsius >= self.TEMP_WARM_MAX:
            status = ThermalStatus.WARM
        else:
            status = ThermalStatus.NORMAL
        
        return {
            "device_serial": device_serial,
            "battery_temp": temp_celsius,
            "status": status.value,
            "thresholds": {
                "normal_max": self.TEMP_NORMAL_MAX,
                "warm_max": self.TEMP_WARM_MAX,
                "hot_max": self.TEMP_HOT_MAX,
                "critical": self.TEMP_CRITICAL,
            },
            "recommendation": self._get_thermal_recommendation(status),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _get_thermal_recommendation(self, status: ThermalStatus) -> str:
        """Get recommendation based on thermal status."""
        recommendations = {
            ThermalStatus.NORMAL: "Operating within normal parameters.",
            ThermalStatus.WARM: "Device is warming. Monitor closely.",
            ThermalStatus.HOT: "Device is hot. Consider reducing load.",
            ThermalStatus.CRITICAL: "CRITICAL: Stop all operations immediately!",
        }
        return recommendations.get(status, "Unknown status.")
    
    async def record_reading(
        self, 
        device_serial: str, 
        battery_info: dict,
        thermal_info: dict
    ):
        """
        Record a hardware reading for historical analysis.
        
        Args:
            device_serial: Device identifier
            battery_info: Battery status dict
            thermal_info: Thermal status dict
        """
        reading = {
            "device_serial": device_serial,
            "battery_level": battery_info.get("level"),
            "battery_voltage": battery_info.get("voltage"),
            "battery_temp": thermal_info.get("battery_temp"),
            "thermal_status": thermal_info.get("status"),
            "charging_status": battery_info.get("status"),
            "recorded_at": datetime.utcnow().isoformat(),
        }
        
        # Store in memory
        if device_serial not in self.device_readings:
            self.device_readings[device_serial] = []
        self.device_readings[device_serial].append(reading)
        
        # Keep only last 100 readings per device
        self.device_readings[device_serial] = self.device_readings[device_serial][-100:]
        
        # Store in database
        try:
            self.supabase.table("device_health_logs").insert(reading).execute()
        except Exception:
            pass  # Table might not exist yet
    
    async def check_all_devices(self, device_serials: list[str]) -> dict:
        """
        Check hardware status of multiple devices.
        
        Args:
            device_serials: List of device serials to check
            
        Returns:
            Summary of all device health statuses
        """
        results = {
            "total_devices": len(device_serials),
            "healthy": 0,
            "warming": 0,
            "hot": 0,
            "critical": 0,
            "devices": [],
            "alerts": [],
            "throttle_recommendations": {},
            "checked_at": datetime.utcnow().isoformat(),
        }
        
        for serial in device_serials:
            try:
                battery = await self.get_battery_info(serial)
                thermal = await self.get_thermal_status(serial)
                
                # Record the reading
                await self.record_reading(serial, battery, thermal)
                
                device_result = {
                    "serial": serial,
                    "battery_level": battery.get("level"),
                    "battery_temp": thermal.get("battery_temp"),
                    "thermal_status": thermal.get("status"),
                    "recommendation": thermal.get("recommendation"),
                }
                results["devices"].append(device_result)
                
                # Categorize by status
                status = thermal.get("status")
                if status == ThermalStatus.NORMAL.value:
                    results["healthy"] += 1
                elif status == ThermalStatus.WARM.value:
                    results["warming"] += 1
                elif status == ThermalStatus.HOT.value:
                    results["hot"] += 1
                    results["throttle_recommendations"][serial] = {
                        "action": "reduce_load",
                        "reason": "Device temperature exceeds safe threshold",
                        "current_temp": thermal.get("battery_temp"),
                    }
                elif status == ThermalStatus.CRITICAL.value:
                    results["critical"] += 1
                    results["alerts"].append({
                        "severity": "critical",
                        "device": serial,
                        "message": f"Device {serial} at critical temperature: {thermal.get('battery_temp')}°C",
                        "action": "immediate_shutdown",
                    })
                    results["throttle_recommendations"][serial] = {
                        "action": "shutdown",
                        "reason": "Critical temperature - risk of hardware damage",
                        "current_temp": thermal.get("battery_temp"),
                    }
                    
            except Exception as e:
                results["alerts"].append({
                    "severity": "warning",
                    "device": serial,
                    "message": f"Failed to read hardware status: {str(e)}",
                })
        
        self.throttle_recommendations = results["throttle_recommendations"]
        
        return results
    
    async def apply_throttling(self, device_serial: str, action: str) -> dict:
        """
        Apply throttling action to a device.
        
        Args:
            device_serial: Device to throttle
            action: Throttling action (reduce_load, pause_jobs, shutdown)
            
        Returns:
            Result of throttling action
        """
        # Update device status in database
        if action == "shutdown":
            new_status = "OFFLINE"
            reason = "Thermal shutdown - critical temperature"
        elif action == "pause_jobs":
            new_status = "WARNING"
            reason = "Jobs paused - high temperature"
        elif action == "reduce_load":
            new_status = "DEGRADED"
            reason = "Load reduced - elevated temperature"
        else:
            new_status = "ONLINE"
            reason = None
        
        update_data = {
            "adb_status": new_status,
            "last_health_check": datetime.utcnow().isoformat(),
        }
        
        if reason:
            update_data["warning_reason"] = reason
        
        self.supabase.table("devices").update(update_data).eq(
            "serial", device_serial
        ).execute()
        
        # Pause any running jobs on this device
        if action in ["shutdown", "pause_jobs"]:
            self.supabase.table("jobs").update({
                "status": "PAUSED",
                "error_message": f"Device thermal protection: {reason}",
            }).eq("device_serial", device_serial).eq("status", "RUNNING").execute()
        
        return {
            "success": True,
            "device_serial": device_serial,
            "action": action,
            "new_status": new_status,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def auto_protect_devices(self, device_serials: list[str]) -> dict:
        """
        Automatically protect devices based on thermal readings.
        
        This is the main entry point for automated thermal protection.
        
        Args:
            device_serials: Devices to monitor and protect
            
        Returns:
            Summary of actions taken
        """
        # Check all devices
        health_report = await self.check_all_devices(device_serials)
        
        actions_taken = []
        
        # Apply automatic protections
        for serial, recommendation in health_report["throttle_recommendations"].items():
            action = recommendation.get("action")
            
            if action == "shutdown":
                await self.apply_throttling(serial, "shutdown")
                actions_taken.append({
                    "device": serial,
                    "action": "shutdown",
                    "reason": recommendation.get("reason"),
                })
            elif action == "reduce_load":
                await self.apply_throttling(serial, "reduce_load")
                actions_taken.append({
                    "device": serial,
                    "action": "reduce_load",
                    "reason": recommendation.get("reason"),
                })
        
        return {
            "devices_checked": len(device_serials),
            "actions_taken": actions_taken,
            "summary": {
                "healthy": health_report["healthy"],
                "warming": health_report["warming"],
                "hot": health_report["hot"],
                "critical": health_report["critical"],
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def get_device_health_history(
        self, 
        device_serial: str,
        hours: int = 24
    ) -> dict:
        """
        Get health history for a device.
        
        Args:
            device_serial: Device to query
            hours: How many hours of history
            
        Returns:
            Historical health data with trends
        """
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        # Fetch from database
        result = self.supabase.table("device_health_logs").select("*").eq(
            "device_serial", device_serial
        ).gte("recorded_at", since).order("recorded_at").execute()
        
        readings = result.data or []
        
        if not readings:
            return {"error": "No historical data available"}
        
        # Calculate statistics
        temps = [r.get("battery_temp", 0) for r in readings]
        avg_temp = sum(temps) / len(temps) if temps else 0
        max_temp = max(temps) if temps else 0
        min_temp = min(temps) if temps else 0
        
        # Detect thermal events
        thermal_events = [
            r for r in readings 
            if r.get("thermal_status") in [ThermalStatus.HOT.value, ThermalStatus.CRITICAL.value]
        ]
        
        return {
            "device_serial": device_serial,
            "period_hours": hours,
            "readings_count": len(readings),
            "temperature": {
                "average": round(avg_temp, 2),
                "max": round(max_temp, 2),
                "min": round(min_temp, 2),
                "current": temps[-1] if temps else None,
            },
            "thermal_events": len(thermal_events),
            "trend": "increasing" if len(temps) > 1 and temps[-1] > temps[0] else "stable",
            "readings": readings[-20:],  # Last 20 readings
        }
    
    async def generate_maintenance_report(self) -> dict:
        """
        Generate a maintenance report for all devices.
        
        Returns:
            Maintenance recommendations and device health summary
        """
        # Fetch all devices
        result = self.supabase.table("devices").select("serial, name, adb_status").execute()
        devices = result.data or []
        
        device_serials = [d["serial"] for d in devices]
        
        # Check all devices
        health_report = await self.check_all_devices(device_serials)
        
        # Generate recommendations
        recommendations = []
        
        if health_report["critical"] > 0:
            recommendations.append({
                "priority": "urgent",
                "action": "Immediately shut down devices with critical temperatures",
                "affected_count": health_report["critical"],
            })
        
        if health_report["hot"] > 0:
            recommendations.append({
                "priority": "high",
                "action": "Reduce load on hot devices or improve cooling",
                "affected_count": health_report["hot"],
            })
        
        if health_report["warming"] > 0:
            recommendations.append({
                "priority": "medium",
                "action": "Monitor warming devices and ensure adequate ventilation",
                "affected_count": health_report["warming"],
            })
        
        # Check for devices that haven't been checked recently
        stale_devices = []
        for serial in device_serials:
            readings = self.device_readings.get(serial, [])
            if readings:
                last_reading = readings[-1].get("recorded_at", "")
                if last_reading:
                    reading_time = datetime.fromisoformat(last_reading)
                    if datetime.utcnow() - reading_time > timedelta(hours=1):
                        stale_devices.append(serial)
        
        if stale_devices:
            recommendations.append({
                "priority": "low",
                "action": "Run health checks on devices with stale readings",
                "affected_count": len(stale_devices),
            })
        
        return {
            "total_devices": len(devices),
            "health_summary": {
                "healthy": health_report["healthy"],
                "warming": health_report["warming"],
                "hot": health_report["hot"],
                "critical": health_report["critical"],
            },
            "recommendations": recommendations,
            "generated_at": datetime.utcnow().isoformat(),
        }
