"""Plan builder - builds executable plans from job payloads."""

from ..policy.warmup import SessionPlan, build_warmup_plan


def build_session_plan(job_kind: str, payload: dict | None) -> SessionPlan:
    """
    Build a SessionPlan from a job kind and payload.

    Args:
        job_kind: The type of job (e.g., "WARMUP_SESSION", "POST_CONTENT")
        payload: Job-specific parameters

    Returns:
        SessionPlan ready for execution by the bot
    """
    if job_kind == "WARMUP_SESSION":
        day = payload.get("day", 1) if payload else 1
        return build_warmup_plan(None, day)

    elif job_kind == "ACTIVE_ENGAGEMENT":
        # TODO: Build active engagement plan
        return SessionPlan(actions=[], notes="Active engagement plan")

    elif job_kind == "POST_CONTENT":
        # TODO: Build post content plan
        return SessionPlan(actions=[], notes="Post content plan")

    else:
        return SessionPlan(actions=[], notes=f"Unknown job kind: {job_kind}")
