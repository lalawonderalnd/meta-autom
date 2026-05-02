"""Worker module initialization."""

from .celery_app import celery

__all__ = ["celery"]
