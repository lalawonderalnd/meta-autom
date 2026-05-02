"""Celery task routing configuration."""

from typing import Any


def route_task_to_device_queue(args: tuple, kwargs: dict[str, Any]) -> dict[str, str]:
    """Route task to per-device queue based on device_serial kwarg."""
    device_serial = kwargs.get("device_serial", "default")
    return {"queue": f"device.{device_serial}"}


# Task routing map
task_routes = {
    "accfarm.execute_job": route_task_to_device_queue,
}
