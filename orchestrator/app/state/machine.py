"""Account state machine - the most important piece of the orchestrator."""

from datetime import datetime, timezone
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.audit import AuditLogger
from .persistence import StatePersistence
from .transitions import get_allowed_transitions, is_allowed

logger = structlog.get_logger()


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    def __init__(self, from_status: str, to_status: str, allowed: set[str]):
        self.from_status = from_status
        self.to_status = to_status
        self.allowed = allowed
        super().__init__(
            f"Invalid transition from {from_status} to {to_status}. "
            f"Allowed transitions: {allowed}"
        )


class AccountStateMachine:
    """
    Manages account state transitions.

    Every transition is deliberate, logged, and atomic.
    """

    def __init__(self, db: AsyncSession, account_id: UUID):
        self.db = db
        self.account_id = account_id
        self.persistence = StatePersistence(db, account_id)
        self.audit = AuditLogger(db)

    async def _get_current_status(self) -> str:
        """Get the current status of the account."""
        # TODO: Implement - select status from accounts table
        return "NEW"

    async def can_transition_to(self, new_status: str) -> bool:
        """Check if a transition to the given status is allowed."""
        current_status = await self._get_current_status()
        return is_allowed(current_status, new_status)

    async def transition(
        self,
        new_status: str,
        *,
        reason: str,
        actor: str = "system",
        metadata: dict | None = None,
    ) -> None:
        """
        Atomically transition the account to a new status.

        Steps:
          1. Lock the accounts row (SELECT ... FOR UPDATE).
          2. Verify the transition is allowed by the matrix.
          3. Update status + relevant timestamp fields.
          4. Append to audit_log.
          5. Trigger side effects (cancel pending jobs, notify, etc.).

        Raises:
            InvalidTransitionError: If the transition is not allowed.
        """
        # Get current status
        current_status = await self._get_current_status()

        # Verify transition is allowed
        if not is_allowed(current_status, new_status):
            allowed = get_allowed_transitions(current_status)
            raise InvalidTransitionError(current_status, new_status, allowed)

        logger.info(
            "state_transition",
            account_id=str(self.account_id),
            from_status=current_status,
            to_status=new_status,
            reason=reason,
            actor=actor,
        )

        # Update state with optimistic locking
        success = await self.persistence.update_state(
            new_status=new_status,
            reason=reason,
            actor=actor,
            metadata=metadata,
        )

        if not success:
            # Version mismatch - retry logic could go here
            raise RuntimeError("State update failed due to concurrent modification")

        # Append audit log
        await self.persistence.append_audit_log(
            old_status=current_status,
            new_status=new_status,
            reason=reason,
            actor=actor,
            metadata=metadata,
        )

        # Trigger side effects based on the new status
        await self._trigger_side_effects(current_status, new_status)

    async def _trigger_side_effects(self, old_status: str, new_status: str) -> None:
        """Trigger side effects based on the transition."""
        # * → COOLDOWN: cancel all QUEUED jobs, set cooldown_until = now + 24h
        if new_status == "COOLDOWN":
            await self.persistence.cancel_queued_jobs()
            # TODO: Set cooldown_until

        # * → NEEDS_ATTENTION: cancel all QUEUED jobs, send Telegram alert
        elif new_status == "NEEDS_ATTENTION":
            await self.persistence.cancel_queued_jobs()
            # TODO: Send Telegram alert via Notifier

        # * → BANNED: cancel everything, archive proxy as "do not reuse"
        elif new_status == "BANNED":
            await self.persistence.cancel_queued_jobs()
            # TODO: Archive proxy

        # WARMING → ACTIVE: reset warmup_day=7, schedule first ACTIVE-tier job
        elif old_status == "WARMING" and new_status == "ACTIVE":
            # TODO: Reset warmup_day, schedule job
            pass

        # IDLE → ACTIVE: re-schedule periodic engagement jobs
        elif old_status == "IDLE" and new_status == "ACTIVE":
            # TODO: Re-schedule jobs
            pass
