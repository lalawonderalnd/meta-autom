"""Celery beat schedule for periodic tasks."""

from celery.schedules import crontab

beat_schedule = {
    # Every 5 min: scan devices for new clones, update heartbeats
    "device.heartbeat": {
        "task": "accfarm.heartbeat_all_devices",
        "schedule": 300,
    },
    # Every hour: check proxies are alive
    "proxies.health_check": {
        "task": "accfarm.proxy_health_check",
        "schedule": 3600,
    },
    # Every day at 03:00 UTC: progress warmup days for accounts that completed yesterday
    "warmup.advance": {
        "task": "accfarm.advance_warmup_days",
        "schedule": crontab(hour=3, minute=0),
    },
    # Every 15 min: evaluate safety triggers
    "safety.evaluate": {
        "task": "accfarm.evaluate_safety",
        "schedule": 900,
    },
    # Every 6h: dispatch ACTIVE-tier engagement to accounts that haven't run today
    "active.dispatch": {
        "task": "accfarm.dispatch_active_engagement",
        "schedule": 21600,
    },
    # Daily 23:00 UTC: send daily ops report to Telegram
    "ops.daily_report": {
        "task": "accfarm.send_daily_ops_report",
        "schedule": crontab(hour=23, minute=0),
    },
}
