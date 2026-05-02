"""Celery application configuration."""

from celery import Celery

from ..config import get_settings

settings = get_settings()

celery = Celery(
    "accfarm",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Configure Celery
celery.conf.update(
    # Task routing - route to per-device queues
    task_routes={
        "accfarm.execute_job": (
            lambda args, kwargs: {"queue": f"device.{kwargs.get('device_serial', 'default')}"}
        ),
    },
    # Reliability settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,  # No prefetching - fairness
    task_track_started=True,
    # Time limits
    task_time_limit=1800,  # 30 min hard kill
    task_soft_time_limit=1500,  # 25 min soft warn
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    # Timezone
    timezone="UTC",
    enable_utc=True,
)

# Load beat schedule
from . import beat_schedule  # noqa: F401

celery.conf.beat_schedule = beat_schedule.beat_schedule
