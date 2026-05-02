"""Job kinds enumeration."""

from enum import StrEnum


class JobKind(StrEnum):
    """Types of jobs that can be dispatched."""

    WARMUP_SESSION = "WARMUP_SESSION"
    ACTIVE_ENGAGEMENT = "ACTIVE_ENGAGEMENT"
    POST_CONTENT = "POST_CONTENT"
    PROFILE_UPDATE = "PROFILE_UPDATE"
    HEALTH_CHECK = "HEALTH_CHECK"
