"""Base action class and result model."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class ActionResult(BaseModel):
    """Result of executing a single action."""

    success: bool
    duration_ms: int
    action_name: str
    metadata: dict[str, Any] = {}
    warning: str | None = None  # e.g., "rate_limit", "checkpoint"
    error: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "duration_ms": 4500,
                    "action_name": "like_post",
                    "metadata": {"liked": 5, "skipped": 2},
                }
            ]
        }
    }


class Action(ABC):
    """Abstract base class for all actions."""

    name: ClassVar[str]

    def __init__(self, session: U2Session, account: "Account"):
        self.session = session
        self.account = account
        self.daily_cap_remaining: int | None = None

    @abstractmethod
    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        """
        Execute the action.

        Args:
            params: Action-specific parameters
            max_count: Maximum number of times to perform this action
            max_duration: Maximum duration in seconds (optional)

        Returns:
            ActionResult - never raises except for CheckpointDetectedError
        """
        pass

    def _ensure_at(self, screen: str) -> None:
        """
        Navigate to the right screen if not already there.

        Args:
            screen: One of "home", "explore", "profile", "reels", "messages"
        """
        logger.debug(f"Ensuring at screen: {screen}")
        # Implementation delegated to InstagramApp in runner

    def _check_for_warnings(self) -> str | None:
        """
        Check for Instagram warnings after an action.

        Returns:
            Warning kind if seen (e.g., "rate_limit"), else None
        """
        if self.session.is_at_checkpoint():
            return "checkpoint"

        # Check for rate limit message
        try:
            hierarchy = self.session.dump_hierarchy().lower()
            if "try again later" in hierarchy or "we limit how often" in hierarchy:
                logger.warning("Rate limit detected")
                return "rate_limit"
        except Exception:
            pass

        return None

    def _sleep_transition(self, mean_seconds: float = 1.5) -> None:
        """Human-like transition sleep between actions."""
        self.session.sleep(mean_seconds)

    def _record_action_event(
        self, event_type: str, details: dict[str, Any] | None = None
    ) -> None:
        """Record an action event for the live stream (via callback)."""
        # This is called by the runner which has access to the event_callback
        pass
