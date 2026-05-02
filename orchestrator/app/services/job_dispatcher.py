"""Job dispatcher - translates intents into Job rows + Celery enqueue."""

import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from accfarm_shared.db_models import Account, Job, Device, Session
from accfarm_shared.enums import AccountStatus, JobKind, JobStatus
from accfarm_shared.models import Job as JobResponse
from ..policy.warmup import build_warmup_plan
from ..policy.posting import POSTING_WINDOWS
from ..policy.limits import get_limits_for_status

logger = structlog.get_logger()


class InvalidJobForStatusError(Exception):
    """Raised when a job kind is not allowed for the account's current status."""

    pass


class DailyLimitExceededError(Exception):
    """Raised when daily limits have been exceeded for the account."""

    pass


class JobDispatcher:
    """
    Translates high-level requests into Job rows and Celery enqueues.

    Behaviors:
    - Refuses to dispatch if account status doesn't allow the kind
    - Refuses if daily limits already hit
    - Auto-fills scheduled_for based on POSTING_WINDOWS if kind=POST_CONTENT
    - Persists Job row first, then enqueues Celery task
    """

    # Mapping of job kinds to allowed account statuses
    JOB_KIND_ALLOWED_STATUSES = {
        JobKind.WARMUP_SESSION: {AccountStatus.NEW, AccountStatus.WARMING},
        JobKind.ACTIVE_ENGAGEMENT: {AccountStatus.ACTIVE},
        JobKind.POST_CONTENT: {AccountStatus.ACTIVE},
        JobKind.PROFILE_UPDATE: {AccountStatus.WARMING, AccountStatus.ACTIVE},
        JobKind.HEALTH_CHECK: {AccountStatus.COOLDOWN, AccountStatus.WARNING, AccountStatus.NEEDS_ATTENTION},
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def dispatch(
        self,
        kind: str,
        account_id: UUID,
        *,
        payload: dict | None = None,
        priority: int = 5,
        scheduled_for: datetime | None = None,
    ) -> dict:
        """
        Dispatch a single job for an account.

        Returns the created Job dict.
        """
        # 1. Load account and check status
        result = await self.db.execute(select(Account).where(Account.id == account_id))
        account = result.scalar_one_or_none()
        
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # 2. Validate job kind is allowed for status
        job_kind = JobKind(kind)
        allowed_statuses = self.JOB_KIND_ALLOWED_STATUSES.get(job_kind)
        
        if allowed_statuses and account.status not in allowed_statuses:
            raise InvalidJobForStatusError(
                f"Job kind {kind} not allowed for account status {account.status.value}"
            )
        
        # 3. Check daily limits
        if kind in (JobKind.WARMUP_SESSION, JobKind.ACTIVE_ENGAGEMENT, JobKind.POST_CONTENT):
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            limits = get_limits_for_status(account.status.value, account.warmup_day if account.status == AccountStatus.WARMING else None)
            
            stmt = select(func.count(Job.id)).where(
                Job.account_id == account_id,
                Job.kind == job_kind,
                Job.scheduled_for >= today_start,
                Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.SUCCESS])
            )
            result = await self.db.execute(stmt)
            count_today = result.scalar_one() or 0
            
            if count_today >= limits.sessions_per_day:
                raise DailyLimitExceededError(
                    f"Daily limit of {limits.sessions_per_day} sessions exceeded for account {account.username}"
                )
        
        # 4. Auto-fill scheduled_for if POST_CONTENT
        if job_kind == JobKind.POST_CONTENT and not scheduled_for:
            now = datetime.now(timezone.utc)
            # Map AccountStatus to niche for posting window lookup
            # In production, this would use the account's actual niche
            window_options = [(9, 11), (14, 16), (19, 21)]  # default windows
            import random
            window = random.choice(window_options)
            hour_offset = random.randint(window[0], window[1] - 1)
            scheduled_for = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=max(0, hour_offset - now.hour))
        
        # 5. Create Job row
        job = Job(
            kind=job_kind,
            account_id=account_id,
            device_id=account.device_id,
            status=JobStatus.QUEUED,
            priority=priority,
            payload=payload or {},
            scheduled_for=scheduled_for or datetime.now(timezone.utc),
        )
        
        self.db.add(job)
        await self.db.flush()
        
        logger.info(
            "job_dispatched",
            job_id=str(job.id),
            kind=kind,
            account_id=str(account_id),
            priority=priority,
            scheduled_for=scheduled_for.isoformat() if scheduled_for else None,
        )
        
        # 6. Enqueue Celery task (done automatically by beat/worker picking up QUEUED jobs)
        return JobResponse.model_validate(job).model_dump()

    async def dispatch_bulk(
        self,
        kind: str,
        account_ids: list[UUID],
        *,
        payload: dict | None = None,
        stagger_seconds: int = 30,
    ) -> list[dict]:
        """
        Bulk dispatch with stagger.

        Spreads job start times to avoid thundering herd.
        """
        jobs = []
        base_time = datetime.now(timezone.utc)

        for i, account_id in enumerate(account_ids):
            scheduled_for = base_time + timedelta(seconds=i * stagger_seconds)
            try:
                job = await self.dispatch(
                    kind=kind,
                    account_id=account_id,
                    payload=payload,
                    scheduled_for=scheduled_for,
                )
                jobs.append(job)
            except (InvalidJobForStatusError, DailyLimitExceededError) as e:
                logger.warning("bulk_dispatch_skipped", account_id=str(account_id), reason=str(e))

        return jobs

    async def cancel_all_for_device(self, device_id: UUID) -> int:
        """Cancel all QUEUED/RUNNING jobs for a device."""
        stmt = select(Job).where(
            Job.device_id == device_id,
            Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING])
        )
        result = await self.db.execute(stmt)
        jobs = result.scalars().all()
        
        cancelled = 0
        for job in jobs:
            job.status = JobStatus.CANCELLED
            job.error_message = "Cancelled via killswitch"
            cancelled += 1
        
        await self.db.flush()
        logger.info("killswitch_triggered", device_id=str(device_id), cancelled_jobs=cancelled)
        return cancelled

    async def dispatch_active_engagement(self) -> dict:
        """Dispatch ACTIVE-tier engagement to accounts that haven't run today."""
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Find ACTIVE accounts that haven't had a session today
        subq = select(Session.account_id, func.max(Session.started_at).label('last_session')).where(
            Session.started_at >= today_start
        ).group_by(Session.account_id).subquery()
        
        stmt = select(Account).where(
            Account.status == AccountStatus.ACTIVE,
            ~select(1).where(
                subq.c.account_id == Account.id,
                subq.c.last_session >= today_start
            ).exists()
        )
        result = await self.db.execute(stmt)
        accounts = result.scalars().all()
        
        dispatched = 0
        for account in accounts:
            try:
                await self.dispatch(
                    kind=JobKind.ACTIVE_ENGAGEMENT,
                    account_id=account.id,
                )
                dispatched += 1
            except (InvalidJobForStatusError, DailyLimitExceededError):
                continue
        
        return {"dispatched": dispatched}
