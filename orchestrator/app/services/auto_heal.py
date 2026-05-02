"""
Auto-healing worker for Meta Autom Farm.

Monitors jobs and accounts for stuck states, crashes, or anomalies,
and automatically attempts recovery actions.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

from ..models import AccountStatus, JobStatus, DeviceStatus
from ..services.account_service import AccountService
from ..services.job_service import JobService
from ..services.device_service import DeviceService
from ..db.session import get_db_session

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Available recovery actions."""
    RESTART_JOB = "restart_job"
    RESET_ACCOUNT = "reset_account"
    KILL_APP = "kill_app"
    REBOOT_DEVICE = "reboot_device"
    CLEAR_DATA = "clear_data"
    ROTATE_PROXY = "rotate_proxy"
    SKIP_DAY = "skip_day"


class AutoHealConfig:
    """Configuration for auto-healing behavior."""
    
    # Time thresholds
    JOB_STUCK_THRESHOLD_MINUTES = 30  # Job running longer than expected
    ACCOUNT_IDLE_THRESHOLD_MINUTES = 45  # Account not progressing
    DEVICE_HEARTBEAT_TIMEOUT_MINUTES = 10  # Device not sending heartbeats
    
    # Retry limits
    MAX_JOB_RETRIES = 3  # Max times to restart a job
    MAX_ACCOUNT_RESETS_PER_DAY = 2  # Max resets per account per day
    
    # Actions by scenario
    STUCK_JOB_ACTIONS = [RecoveryAction.RESTART_JOB]
    IDLE_ACCOUNT_ACTIONS = [RecoveryAction.KILL_APP, RecoveryAction.RESET_ACCOUNT]
    DEAD_DEVICE_ACTIONS = [RecoveryAction.REBOOT_DEVICE]
    CRASH_LOOP_ACTIONS = [RecoveryAction.CLEAR_DATA, RecoveryAction.SKIP_DAY]
    
    # Panic mode thresholds
    PANIC_ERROR_COUNT = 5  # Errors across farm before panic mode
    PANIC_WINDOW_MINUTES = 15  # Time window for error counting


class AutoHealingWorker:
    """
    Background worker that monitors and heals stuck jobs/accounts/devices.
    
    Runs continuously and performs:
    - Stuck job detection and restart
    - Idle account recovery
    - Dead device reboot requests
    - Crash loop detection and mitigation
    - Panic mode activation when error rates spike
    """
    
    def __init__(self, config: Optional[AutoHealConfig] = None):
        self.config = config or AutoHealConfig()
        self.running = False
        self.panic_mode = False
        self.panic_mode_until: Optional[datetime] = None
        self.error_counts: Dict[str, List[datetime]] = {}  # device_id -> error timestamps
        
    async def start(self, interval_seconds: int = 60):
        """Start the auto-healing worker."""
        logger.info("Auto-healing worker starting")
        self.running = True
        
        while self.running:
            try:
                await self._heal_cycle()
            except Exception as e:
                logger.exception(f"Error in heal cycle: {e}")
            
            await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop the auto-healing worker."""
        self.running = False
        logger.info("Auto-healing worker stopped")
    
    async def _heal_cycle(self):
        """Run one complete healing cycle."""
        async with get_db_session() as db:
            # Check for panic mode expiry
            if self.panic_mode and self.panic_mode_until:
                if datetime.utcnow() > self.panic_mode_until:
                    self.panic_mode = False
                    logger.info("Panic mode deactivated")
                else:
                    logger.debug("Panic mode active, skipping healing")
                    return
            
            # Run all healing checks
            await self._check_stuck_jobs(db)
            await self._check_idle_accounts(db)
            await self._check_dead_devices(db)
            await self._check_crash_loops(db)
    
    async def _check_stuck_jobs(self, db):
        """Find and restart stuck jobs."""
        stuck_threshold = datetime.utcnow() - timedelta(
            minutes=self.config.JOB_STUCK_THRESHOLD_MINUTES
        )
        
        # Find jobs that are RUNNING but haven't updated recently
        stuck_jobs = await JobService.get_stuck_jobs(
            db, 
            last_updated_before=stuck_threshold
        )
        
        for job in stuck_jobs:
            if self.panic_mode:
                break
                
            retry_count = job.retry_count or 0
            if retry_count >= self.config.MAX_JOB_RETRIES:
                logger.warning(
                    f"Job {job.id} exceeded max retries ({retry_count}), "
                    f"marking as failed"
                )
                await JobService.fail_job(db, job.id, reason="Max retries exceeded")
                continue
            
            logger.info(
                f"Job {job.id} stuck on account {job.account_id}, "
                f"attempting restart (retry {retry_count + 1})"
            )
            
            await self._execute_recovery(
                db, 
                RecoveryAction.RESTART_JOB,
                job_id=job.id
            )
    
    async def _check_idle_accounts(self, db):
        """Find and recover idle accounts."""
        idle_threshold = datetime.utcnow() - timedelta(
            minutes=self.config.ACCOUNT_IDLE_THRESHOLD_MINUTES
        )
        
        idle_accounts = await AccountService.get_idle_accounts(
            db,
            last_activity_before=idle_threshold,
            statuses=[AccountStatus.ACTIVE, AccountStatus.WARMUP]
        )
        
        for account in idle_accounts:
            if self.panic_mode:
                break
            
            # Check reset count for today
            resets_today = await AccountService.get_reset_count_today(db, account.id)
            if resets_today >= self.config.MAX_ACCOUNT_RESETS_PER_DAY:
                logger.warning(
                    f"Account {account.id} exceeded daily reset limit, "
                    f"skipping recovery"
                )
                continue
            
            logger.info(f"Account {account.id} idle, attempting recovery")
            
            # Try kill app first, then reset if still idle
            await self._execute_recovery(
                db,
                RecoveryAction.KILL_APP,
                account_id=account.id
            )
    
    async def _check_dead_devices(self, db):
        """Find and request reboot for dead devices."""
        heartbeat_timeout = datetime.utcnow() - timedelta(
            minutes=self.config.DEVICE_HEARTBEAT_TIMEOUT_MINUTES
        )
        
        dead_devices = await DeviceService.get_devices_without_heartbeat(
            db,
            last_heartbeat_before=heartbeat_timeout
        )
        
        for device in dead_devices:
            if self.panic_mode:
                break
            
            logger.warning(
                f"Device {device.id} ({device.name}) appears dead, "
                f"requesting reboot"
            )
            
            await self._execute_recovery(
                db,
                RecoveryAction.REBOOT_DEVICE,
                device_id=device.id
            )
    
    async def _check_crash_loops(self, db):
        """Detect accounts/jobs in crash loops and mitigate."""
        # Find accounts with multiple recent failures
        crash_loop_accounts = await AccountService.get_crash_loop_accounts(
            db,
            failure_count=3,
            window_minutes=30
        )
        
        for account in crash_loop_accounts:
            if self.panic_mode:
                break
            
            logger.warning(
                f"Account {account.id} in crash loop, clearing data and skipping day"
            )
            
            await self._execute_recovery(
                db,
                RecoveryAction.CLEAR_DATA,
                account_id=account.id
            )
            await self._execute_recovery(
                db,
                RecoveryAction.SKIP_DAY,
                account_id=account.id
            )
    
    async def _execute_recovery(
        self,
        db,
        action: RecoveryAction,
        job_id: Optional[int] = None,
        account_id: Optional[int] = None,
        device_id: Optional[int] = None
    ):
        """Execute a recovery action."""
        try:
            if action == RecoveryAction.RESTART_JOB:
                if job_id:
                    await JobService.restart_job(db, job_id)
                    self._record_error(device_id)
                    
            elif action == RecoveryAction.RESET_ACCOUNT:
                if account_id:
                    await AccountService.reset_account(db, account_id)
                    
            elif action == RecoveryAction.KILL_APP:
                if account_id:
                    await AccountService.kill_app(db, account_id)
                    
            elif action == RecoveryAction.REBOOT_DEVICE:
                if device_id:
                    await DeviceService.request_reboot(db, device_id)
                    
            elif action == RecoveryAction.CLEAR_DATA:
                if account_id:
                    await AccountService.clear_app_data(db, account_id)
                    
            elif action == RecoveryAction.ROTATE_PROXY:
                if account_id:
                    await AccountService.rotate_proxy(db, account_id)
                    
            elif action == RecoveryAction.SKIP_DAY:
                if account_id:
                    await AccountService.skip_warmup_day(db, account_id)
            
            logger.info(f"Recovery action {action.value} executed successfully")
            
        except Exception as e:
            logger.error(f"Recovery action {action.value} failed: {e}")
            self._record_error(device_id)
            self._check_panic_mode()
    
    def _record_error(self, device_id: Optional[int]):
        """Record an error for panic mode tracking."""
        if not device_id:
            return
        
        now = datetime.utcnow()
        if device_id not in self.error_counts:
            self.error_counts[device_id] = []
        
        self.error_counts[device_id].append(now)
        
        # Clean old errors outside the window
        cutoff = now - timedelta(minutes=self.config.PANIC_WINDOW_MINUTES)
        self.error_counts[device_id] = [
            ts for ts in self.error_counts[device_id] if ts > cutoff
        ]
    
    def _check_panic_mode(self):
        """Check if panic mode should be activated."""
        total_recent_errors = sum(
            len(errors) for errors in self.error_counts.values()
        )
        
        if total_recent_errors >= self.config.PANIC_ERROR_COUNT:
            self.panic_mode = True
            self.panic_mode_until = datetime.utcnow() + timedelta(
                minutes=self.config.PANIC_WINDOW_MINUTES * 2
            )
            logger.critical(
                f"PANIC MODE ACTIVATED: {total_recent_errors} errors detected. "
                f"Pausing healing until {self.panic_mode_until}"
            )


# Service methods to support auto-healing
class AccountServiceHealingMixin:
    """Mixin adding healing-related methods to AccountService."""
    
    @staticmethod
    async def get_idle_accounts(db, last_activity_before: datetime, statuses: List[AccountStatus]):
        """Get accounts that haven't progressed recently."""
        from sqlalchemy import select
        from ..models import Account
        
        stmt = select(Account).where(
            Account.last_activity_at < last_activity_before,
            Account.status.in_(statuses)
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_reset_count_today(db, account_id: int) -> int:
        """Count how many times an account was reset today."""
        from sqlalchemy import select, func
        from ..models import AccountEvent, EventType
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.count()).select_from(AccountEvent).where(
            AccountEvent.account_id == account_id,
            AccountEvent.event_type == EventType.RESET,
            AccountEvent.created_at >= today_start
        )
        result = await db.execute(stmt)
        return result.scalar() or 0
    
    @staticmethod
    async def get_crash_loop_accounts(db, failure_count: int, window_minutes: int) -> List[Any]:
        """Get accounts with multiple recent failures."""
        from sqlalchemy import select, func
        from ..models import Account, AccountEvent, EventType
        
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        stmt = (
            select(AccountEvent.account_id, func.count().label('failure_count'))
            .where(
                AccountEvent.event_type == EventType.FAILURE,
                AccountEvent.created_at >= window_start
            )
            .group_by(AccountEvent.account_id)
            .having(func.count() >= failure_count)
        )
        result = await db.execute(stmt)
        
        account_ids = [row.account_id for row in result.all()]
        if not account_ids:
            return []
        
        stmt = select(Account).where(Account.id.in_(account_ids))
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def reset_account(db, account_id: int):
        """Reset an account to a clean state."""
        from ..models import Account, AccountStatus
        from sqlalchemy import update
        
        stmt = update(Account).where(Account.id == account_id).values(
            status=AccountStatus.NEW,
            current_warmup_day=0,
            last_activity_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()
        
        # Log event
        from ..models import AccountEvent, EventType
        event = AccountEvent(
            account_id=account_id,
            event_type=EventType.RESET,
            details={"reason": "auto_heal"}
        )
        db.add(event)
        await db.commit()
    
    @staticmethod
    async def kill_app(db, account_id: int):
        """Request killing the Instagram app for an account."""
        from ..models import Account
        from sqlalchemy import select
        
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account and account.device_id:
            # Send command to device layer via job queue
            from ..models import Job, JobType, JobPriority
            job = Job(
                account_id=account_id,
                device_id=account.device_id,
                job_type=JobType.KILL_APP,
                priority=JobPriority.HIGH,
                payload={"package": account.clone_package}
            )
            db.add(job)
            await db.commit()
    
    @staticmethod
    async def clear_app_data(db, account_id: int):
        """Request clearing app data for an account."""
        from ..models import Account
        from sqlalchemy import select
        
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account and account.device_id:
            from ..models import Job, JobType, JobPriority
            job = Job(
                account_id=account_id,
                device_id=account.device_id,
                job_type=JobType.CLEAR_DATA,
                priority=JobPriority.HIGH,
                payload={"package": account.clone_package}
            )
            db.add(job)
            await db.commit()
    
    @staticmethod
    async def rotate_proxy(db, account_id: int):
        """Rotate proxy for an account."""
        from ..models import Account
        from sqlalchemy import select, update
        from ...shared.proxy_manager import ProxyManager
        
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account:
            proxy_mgr = ProxyManager()
            new_proxy = await proxy_mgr.get_available_proxy(exclude_ids=[account.proxy_id])
            if new_proxy:
                stmt = update(Account).where(Account.id == account_id).values(
                    proxy_id=new_proxy.id
                )
                await db.execute(stmt)
                await db.commit()
    
    @staticmethod
    async def skip_warmup_day(db, account_id: int):
        """Skip current warmup day and move to next."""
        from ..models import Account
        from sqlalchemy import select, update
        
        stmt = select(Account).where(Account.id == account_id)
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if account:
            new_day = min((account.current_warmup_day or 0) + 2, 7)
            stmt = update(Account).where(Account.id == account_id).values(
                current_warmup_day=new_day,
                last_activity_at=datetime.utcnow()
            )
            await db.execute(stmt)
            await db.commit()


class JobServiceHealingMixin:
    """Mixin adding healing-related methods to JobService."""
    
    @staticmethod
    async def get_stuck_jobs(db, last_updated_before: datetime) -> List[Any]:
        """Get jobs that appear stuck."""
        from sqlalchemy import select
        from ..models import Job, JobStatus
        
        stmt = select(Job).where(
            Job.status == JobStatus.RUNNING,
            Job.updated_at < last_updated_before
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def restart_job(db, job_id: int):
        """Restart a stuck job."""
        from ..models import Job, JobStatus
        from sqlalchemy import select, update
        
        stmt = select(Job).where(Job.id == job_id)
        result = await db.execute(stmt)
        job = result.scalar_one_or_none()
        
        if job:
            # Increment retry count
            new_retry_count = (job.retry_count or 0) + 1
            
            # Reset job to pending
            stmt = update(Job).where(Job.id == job_id).values(
                status=JobStatus.PENDING,
                retry_count=new_retry_count,
                started_at=None,
                completed_at=None,
                error=None,
                updated_at=datetime.utcnow()
            )
            await db.execute(stmt)
            await db.commit()
            
            # Log event
            from ..models import JobEvent, JobEventType
            event = JobEvent(
                job_id=job_id,
                event_type=JobEventType.RESTARTED,
                details={"retry_count": new_retry_count}
            )
            db.add(event)
            await db.commit()
    
    @staticmethod
    async def fail_job(db, job_id: int, reason: str):
        """Mark a job as failed."""
        from ..models import Job, JobStatus
        from sqlalchemy import update
        
        stmt = update(Job).where(Job.id == job_id).values(
            status=JobStatus.FAILED,
            error=reason,
            completed_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        await db.execute(stmt)
        await db.commit()


class DeviceServiceHealingMixin:
    """Mixin adding healing-related methods to DeviceService."""
    
    @staticmethod
    async def get_devices_without_heartbeat(db, last_heartbeat_before: datetime) -> List[Any]:
        """Get devices that haven't sent heartbeats recently."""
        from sqlalchemy import select
        from ..models import Device, DeviceStatus
        
        stmt = select(Device).where(
            Device.last_heartbeat_at < last_heartbeat_before,
            Device.status == DeviceStatus.ONLINE
        )
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def request_reboot(db, device_id: int):
        """Request a device reboot."""
        from ..models import Device, DeviceStatus
        from sqlalchemy select, update
        
        stmt = update(Device).where(Device.id == device_id).values(
            status=DeviceStatus.REBOOTING,
            requested_action="reboot"
        )
        await db.execute(stmt)
        await db.commit()
        
        # Create a high-priority job to trigger the reboot
        from ..models import Job, JobType, JobPriority
        job = Job(
            device_id=device_id,
            job_type=JobType.REBOOT_DEVICE,
            priority=JobPriority.CRITICAL,
            payload={}
        )
        db.add(job)
        await db.commit()
