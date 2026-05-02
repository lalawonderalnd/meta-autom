"""Shared enums used across all layers."""

from enum import Enum


class AccountStatus(str, Enum):
    """Account lifecycle status."""

    NEW = "NEW"  # Just imported, no warmup yet
    WARMING = "WARMING"  # In warmup curriculum (days 1-7)
    ACTIVE = "ACTIVE"  # Healthy, posting/engaging
    IDLE = "IDLE"  # Manually paused
    COOLDOWN = "COOLDOWN"  # Auto-paused after suspicious signal
    NEEDS_ATTENTION = "NEEDS_ATTENTION"  # Captcha / verification needed
    WARNING = "WARNING"  # IG threw a soft warning
    SHADOWBANNED = "SHADOWBANNED"  # Detected reduced reach
    BANNED = "BANNED"  # Hard ban, dead
    REMOVED = "REMOVED"  # Operator marked for removal


class Platform(str, Enum):
    """Social media platform."""

    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"


class DeviceStatus(str, Enum):
    """Device availability status."""

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    BUSY = "BUSY"
    ERROR = "ERROR"


class JobStatus(str, Enum):
    """Job execution status."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobKind(str, Enum):
    """Types of jobs the orchestrator can dispatch."""

    WARMUP_SESSION = "WARMUP_SESSION"
    POST_CONTENT = "POST_CONTENT"
    ENGAGE_HASHTAG = "ENGAGE_HASHTAG"
    ENGAGE_FOLLOWERS = "ENGAGE_FOLLOWERS"
    WATCH_STORIES = "WATCH_STORIES"
    CHECK_HEALTH = "CHECK_HEALTH"
    RECOVER_CHECKPOINT = "RECOVER_CHECKPOINT"
