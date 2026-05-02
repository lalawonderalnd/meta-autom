"""Telegram notifier for ops alerts."""

import structlog
import httpx

logger = structlog.get_logger()


class Notifier:
    """Sends Telegram alerts to ops."""

    def __init__(self, db):
        self.db = db

    async def send_alert(self, message: str, severity: str = "info") -> bool:
        """Send an alert to the ops Telegram channel."""
        # TODO: Implement - call Telegram Bot API
        logger.info("alert_sent", severity=severity, message=message[:100])
        return True

    async def send_daily_report(self) -> dict:
        """Send daily ops report to Telegram."""
        # TODO: Implement - gather stats, format report, send
        return {"sent": False, "reason": "Not implemented"}

    async def notify_checkpoint(self, account_id: str, checkpoint_type: str) -> None:
        """Notify ops of a checkpoint detected on an account."""
        message = f"⚠️ Checkpoint detected on account {account_id}: {checkpoint_type}"
        await self.send_alert(message, severity="warning")

    async def notify_ban(self, account_id: str, reason: str) -> None:
        """Notify ops of a banned account."""
        message = f"🚫 Account {account_id} banned: {reason}"
        await self.send_alert(message, severity="critical")

    async def notify_panic_mode(self, enabled: bool, reason: str) -> None:
        """Notify ops of panic mode state change."""
        state = "ENABLED" if enabled else "DISABLED"
        message = f"🚨 PANIC MODE {state}: {reason}"
        await self.send_alert(message, severity="critical")
