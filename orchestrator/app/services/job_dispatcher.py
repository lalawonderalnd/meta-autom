"""Job dispatcher - translates intents into Job rows + Celery enqueue."""

import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
        "WARMUP_SESSION": {"NEW", "WARMING"},
        "ACTIVE_ENGAGEMENT": {"ACTIVE"},
        "POST_CONTENT": {"ACTIVE"},
        "PROFILE_UPDATE": {"WARMING", "ACTIVE"},
        "HEALTH_CHECK": {"COOLDOWN", "WARNING", "NEEDS_ATTENTION"},
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
        # TODO: Implement full dispatch logic
        # 1. Load account and check status
        # 2. Validate job kind is allowed for status
        # 3. Check daily limits
        # 4. Auto-fill scheduled_for if POST_CONTENT
        # 5. Create Job row
        # 6. Enqueue Celery task

        logger.info(
            "job_dispatched",
            kind=kind,
            account_id=str(account_id),
            priority=priority,
        )

        # Placeholder return
        return {
            "id": "job-uuid-placeholder",
            "kind": kind,
            "account_id": str(account_id),
            "status": "QUEUED",
            "priority": priority,
            "scheduled_for": scheduled_for.isoformat() if scheduled_for else None,
        }

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
        # TODO: Implement
        return 0

    async def dispatch_active_engagement(self) -> dict:
        """Dispatch ACTIVE-tier engagement to accounts that haven't run today."""
        # TODO: Implement
        return {"dispatched": 0}
