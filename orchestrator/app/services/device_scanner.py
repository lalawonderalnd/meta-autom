"""Device scanner - polls phones for new clones."""

import structlog
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from accfarm_shared.db_models import Device, Account, Session
from accfarm_shared.enums import DeviceStatus, AccountStatus

logger = structlog.get_logger()


class DeviceScanner:
    """Polls devices for new clones and updates heartbeats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_device(self, device_id: UUID) -> dict:
        """Trigger a clone scan for a specific device.
        
        In production, this would call the Device Layer API to:
        1. ADB connect to the device
        2. Run `pm list packages | grep instagram` to find all clones
        3. Create Account rows for any new clones found
        
        For now, we simulate by updating the device's last_heartbeat.
        """
        logger.info("device_scan_triggered", device_id=str(device_id))
        
        # Update device heartbeat
        result = await self.db.execute(
            select(Device).where(Device.id == device_id)
        )
        device = result.scalar_one_or_none()
        
        if not device:
            raise ValueError(f"Device {device_id} not found")
        
        device.last_heartbeat = datetime.now(timezone.utc)
        device.status = DeviceStatus.ONLINE
        
        await self.db.flush()
        
        # TODO: Call Device Layer API to scan for actual clones
        # This would be an HTTP call to http://device-layer:8001/scan/{device_id}
        
        return {"clones_found": 0, "device_status": device.status.value}

    async def heartbeat_all(self) -> dict:
        """Update heartbeats for all registered devices.
        
        In production, this would:
        1. Iterate through all devices
        2. Try ADB connect to each
        3. Update status based on response
        4. Trigger clone scan for responsive devices
        """
        result = await self.db.execute(select(Device))
        devices = result.scalars().all()
        
        devices_checked = 0
        devices_online = 0
        
        for device in devices:
            devices_checked += 1
            # In production: try ADB connect here
            # For now, mark all as online if they were recently seen
            if device.last_heartbeat:
                time_since = datetime.now(timezone.utc) - device.last_heartbeat
                if time_since.total_seconds() < 3600:  # Seen in last hour
                    device.status = DeviceStatus.ONLINE
                    devices_online += 1
                else:
                    device.status = DeviceStatus.OFFLINE
            else:
                device.status = DeviceStatus.OFFLINE
        
        await self.db.flush()
        
        logger.info("heartbeat_completed", checked=devices_checked, online=devices_online)
        return {"devices_checked": devices_checked, "devices_online": devices_online}

    async def register_clones_for_device(
        self, 
        device_id: UUID, 
        package_names: list[str]
    ) -> int:
        """Register new clone accounts found on a device.
        
        Called after scanning a device finds new Instagram clones.
        Creates Account rows with status=NEW for each new package.
        
        Args:
            device_id: The device UUID
            package_names: List of Instagram package names found (e.g., com.instagram.androidp1)
            
        Returns:
            Number of new clones registered
        """
        # Get existing packages for this device
        result = await self.db.execute(
            select(Account.package_name).where(Account.device_id == device_id)
        )
        existing_packages = set(result.scalars().all())
        
        new_count = 0
        for pkg in package_names:
            if pkg not in existing_packages:
                account = Account(
                    platform="instagram",
                    username=f"clone_{pkg}",  # Will be updated after manual login
                    password_encrypted=b"",  # Will be set after credentials added
                    package_name=pkg,
                    device_id=device_id,
                    status=AccountStatus.NEW,
                )
                self.db.add(account)
                new_count += 1
        
        if new_count > 0:
            # Update device's current_clone_count
            device_result = await self.db.execute(
                select(Device).where(Device.id == device_id)
            )
            device = device_result.scalar_one_or_none()
            if device:
                device.current_clone_count += new_count
        
        await self.db.flush()
        logger.info("clones_registered", device_id=str(device_id), new_clones=new_count)
        return new_count
