"""Safety triggers and panic mode logic."""

import structlog
from datetime import datetime, timedelta, timezone

logger = structlog.get_logger()


class SafetyPolicy:
    """
    Globally watched safety signals.

    Triggers:
    - If >10% of ACTIVE accounts on one phone hit COOLDOWN within 1 hour → kill all jobs on that phone
    - If a single proxy hits 3 BANNED accounts → mark proxy as "burned" and quarantine
    - If a single content_item correlates with 5+ WARNINGs → quarantine the content
    - If overall ban rate exceeds 2% per day → enable "panic mode"
    """

    def __init__(self, db):
        self.db = db

    async def evaluate(self) -> dict:
        """Evaluate all safety triggers and take action if needed."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "triggers_checked": 0,
            "actions_taken": [],
        }

        # Check each trigger
        results["triggers_checked"] += 1
        phone_result = await self._check_phone_cooldown_spike()
        if phone_result:
            results["actions_taken"].append(phone_result)

        results["triggers_checked"] += 1
        proxy_result = await self._check_proxy_ban_rate()
        if proxy_result:
            results["actions_taken"].append(proxy_result)

        results["triggers_checked"] += 1
        content_result = await self._check_content_warning_correlation()
        if content_result:
            results["actions_taken"].append(content_result)

        results["triggers_checked"] += 1
        panic_result = await self._check_overall_ban_rate()
        if panic_result:
            results["actions_taken"].append(panic_result)

        return results

    async def _check_phone_cooldown_spike(self) -> dict | None:
        """Check if >10% of ACTIVE accounts on one phone hit COOLDOWN within 1 hour."""
        # TODO: Implement full check
        # Query: count ACTIVE accounts per device, count that went to COOLDOWN in last hour
        # If ratio > 0.10, trigger killswitch
        return None

    async def _check_proxy_ban_rate(self) -> dict | None:
        """Check if a single proxy has 3+ BANNED accounts."""
        # TODO: Implement
        # Query: group banned accounts by proxy_id, find proxies with count >= 3
        # Mark those proxies as "burned"
        return None

    async def _check_content_warning_correlation(self) -> dict | None:
        """Check if a single content_item correlates with 5+ WARNINGs."""
        # TODO: Implement
        # Query: join actions with content_item, filter by warning events
        # Quarantine content items with 5+ warnings
        return None

    async def _check_overall_ban_rate(self) -> dict | None:
        """Check if overall ban rate exceeds 2% per day."""
        # TODO: Implement
        # Query: count total accounts, count accounts banned today
        # If ratio > 0.02, enable panic mode
        return None

    async def is_panic_mode(self) -> bool:
        """Check if panic mode is currently enabled."""
        # TODO: Implement - check a flag in config or cache
        return False

    async def enable_panic_mode(self, reason: str) -> None:
        """Enable panic mode - only WARMING accounts continue, ACTIVE pauses."""
        logger.warning("panic_mode_enabled", reason=reason)
        # TODO: Implement - set flag, pause all ACTIVE account jobs

    async def disable_panic_mode(self) -> None:
        """Disable panic mode."""
        logger.info("panic_mode_disabled")
        # TODO: Implement - clear flag, resume paused jobs
