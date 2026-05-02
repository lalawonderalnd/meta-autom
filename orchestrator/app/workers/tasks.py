"""Celery task definitions."""

import asyncio
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from .celery_app import celery


@celery.task(bind=True, name="accfarm.execute_job")
def execute_job(self, job_id: str, device_serial: str) -> dict[str, Any]:
    """Execute a job on a specific device.

    1. Load Job from DB
    2. Load Account from DB
    3. Build SessionPlan from Job.payload
    4. Acquire DevicePool session for (device, account)
    5. Run accfarm_ig.runner.run_session(session, account, plan)
    6. Persist SessionResult: update account state, record actions, append session row
    7. On any exception: increment attempt, decide retry vs fail per policy
    """
    # Import here to avoid circular imports and allow Celery to start without full app
    from ..config import get_settings
    from ..db import async_session_factory

    settings = get_settings()

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            # TODO: Implement full job execution logic
            # This is a placeholder that ties together Layer 3 (device) and Layer 4 (bot)

            # 1. Load Job from DB
            # job = await db.get(Job, UUID(job_id))
            # if job is None or job.status in ("SUCCESS", "FAILED"):
            #     return {"status": "skipped", "reason": "Job not found or already completed"}

            # 2. Load Account from DB
            # account = await db.get(Account, job.account_id)

            # 3. Build SessionPlan from Job.payload
            # from ..plans.builder import build_session_plan
            # plan = build_session_plan(job.kind, job.payload)

            # 4. Acquire DevicePool session for (device, account)
            # from accfarm_device import DevicePool
            # async with DevicePool().get_session(device_serial, account) as session:

            # 5. Run the bot
            # from accfarm_ig.runner import run_session
            # result = await run_session(session, account, plan)

            # 6. Persist results
            # await persist_session_result(db, result)

            return {
                "status": "completed",
                "job_id": job_id,
                "device_serial": device_serial,
                "result": {"actions_performed": 0},
            }

    return asyncio.run(_run())


@celery.task(name="accfarm.heartbeat_all_devices")
def heartbeat_all_devices() -> dict[str, Any]:
    """Scan devices for new clones and update heartbeats."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            # TODO: Implement via DeviceScanner
            from ..services.device_scanner import DeviceScanner

            scanner = DeviceScanner(db)
            result = await scanner.heartbeat_all()
            return result

    return asyncio.run(_run())


@celery.task(name="accfarm.proxy_health_check")
def proxy_health_check() -> dict[str, Any]:
    """Check all proxies are alive."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            from ..services.proxy_health import ProxyHealth

            health = ProxyHealth(db)
            result = await health.check_all()
            return result

    return asyncio.run(_run())


@celery.task(name="accfarm.advance_warmup_days")
def advance_warmup_days() -> dict[str, Any]:
    """Progress warmup days for accounts that completed yesterday's plan."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            # TODO: Implement
            return {"advanced": 0}

    return asyncio.run(_run())


@celery.task(name="accfarm.evaluate_safety")
def evaluate_safety() -> dict[str, Any]:
    """Evaluate safety triggers and take action if needed."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            from ..policy.safety import SafetyPolicy

            safety = SafetyPolicy(db)
            result = await safety.evaluate()
            return result

    return asyncio.run(_run())


@celery.task(name="accfarm.dispatch_active_engagement")
def dispatch_active_engagement() -> dict[str, Any]:
    """Dispatch ACTIVE-tier engagement to accounts that haven't run today."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            from ..services.job_dispatcher import JobDispatcher

            dispatcher = JobDispatcher(db)
            result = await dispatcher.dispatch_active_engagement()
            return result

    return asyncio.run(_run())


@celery.task(name="accfarm.send_daily_ops_report")
def send_daily_ops_report() -> dict[str, Any]:
    """Send daily ops report to Telegram."""
    from ..config import get_settings
    from ..db import async_session_factory

    async def _run() -> dict[str, Any]:
        async with async_session_factory() as db:
            from ..services.notifier import Notifier

            notifier = Notifier(db)
            result = await notifier.send_daily_report()
            return result

    return asyncio.run(_run())
