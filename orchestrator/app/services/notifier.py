"""Telegram notifier for ops alerts."""

import structlog
import httpx
from typing import Optional

logger = structlog.get_logger()


class Notifier:
    """Sends Telegram alerts to ops."""

    def __init__(self, db, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.db = db
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)

    async def send_alert(self, message: str, severity: str = "info") -> bool:
        """Send an alert to the ops Telegram channel."""
        if not self._enabled:
            logger.debug("telegram_disabled", severity=severity, message=message[:100])
            return False
        
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨",
        }
        emoji = emoji_map.get(severity, "ℹ️")
        
        formatted_message = f"{emoji} *{severity.upper()}*\n\n{message}"
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": formatted_message,
                        "parse_mode": "Markdown",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info("alert_sent", severity=severity, message=message[:100])
                return True
        except Exception as e:
            logger.error("alert_send_failed", severity=severity, error=str(e))
            return False

    async def send_daily_report(self) -> dict:
        """Send daily ops report to Telegram."""
        if not self._enabled:
            return {"sent": False, "reason": "Telegram not configured"}
        
        # Gather stats from DB
        from sqlalchemy import select, func
        from accfarm_shared.db_models import Account, Device, Job, Session
        from accfarm_shared.enums import AccountStatus, JobStatus
        from datetime import datetime, timezone, timedelta
        
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count accounts by status
        result = await self.db.execute(
            select(Account.status, func.count(Account.id)).group_by(Account.status)
        )
        account_counts = dict(result.all())
        
        # Count devices online
        result = await self.db.execute(
            select(func.count(Device.id)).where(Device.status == "online")
        )
        devices_online = result.scalar_one() or 0
        
        result = await self.db.execute(select(func.count(Device.id)))
        devices_total = result.scalar_one() or 0
        
        # Count jobs completed today
        result = await self.db.execute(
            select(func.count(Job.id)).where(
                Job.finished_at >= today_start,
                Job.status == JobStatus.SUCCESS,
            )
        )
        jobs_completed = result.scalar_one() or 0
        
        # Count bans/warnings today
        result = await self.db.execute(
            select(func.count(Account.id)).where(
                Account.updated_at >= today_start,
                Account.status.in_([AccountStatus.BANNED, AccountStatus.WARNING]),
            )
        )
        issues_today = result.scalar_one() or 0
        
        # Format report
        report = f"""*Daily Ops Report* 📊
_Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}_

*Accounts:*
• Total: {sum(account_counts.values())}
• Active: {account_counts.get(AccountStatus.ACTIVE, 0)}
• Warming: {account_counts.get(AccountStatus.WARMING, 0)}
• Issues: {issues_today}

*Devices:*
• Online: {devices_online}/{devices_total}

*Jobs:*
• Completed today: {jobs_completed}

*Issues:*
• Bans/Warnings today: {issues_today}
"""
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
                response = await client.post(
                    url,
                    json={
                        "chat_id": self.chat_id,
                        "text": report,
                        "parse_mode": "Markdown",
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                logger.info("daily_report_sent")
                return {"sent": True, "stats": {"accounts": sum(account_counts.values()), "jobs_completed": jobs_completed}}
        except Exception as e:
            logger.error("daily_report_send_failed", error=str(e))
            return {"sent": False, "error": str(e)}

    async def notify_checkpoint(self, account_id: str, checkpoint_type: str) -> None:
        """Notify ops of a checkpoint detected on an account."""
        message = f"⚠️ Checkpoint detected on account `{account_id}`: {checkpoint_type}"
        await self.send_alert(message, severity="warning")

    async def notify_ban(self, account_id: str, reason: str) -> None:
        """Notify ops of a banned account."""
        message = f"🚫 Account `{account_id}` banned: {reason}"
        await self.send_alert(message, severity="critical")

    async def notify_panic_mode(self, enabled: bool, reason: str) -> None:
        """Notify ops of panic mode state change."""
        state = "*ENABLED*" if enabled else "*DISABLED*"
        message = f"🚨 PANIC MODE {state}\n\nReason: {reason}"
        await self.send_alert(message, severity="critical")

    async def notify_device_offline(self, device_name: str, duration_minutes: int) -> None:
        """Notify ops that a device has been offline for too long."""
        message = f"⚠️ Device `{device_name}` offline for {duration_minutes} minutes"
        await self.send_alert(message, severity="warning")

    async def notify_proxy_dead(self, proxy_id: str, account_count: int) -> None:
        """Notify ops that a proxy is dead."""
        message = f"❌ Proxy `{proxy_id}` is dead. Affects {account_count} accounts."
        await self.send_alert(message, severity="error")
