"""Allowed state transitions matrix for accounts."""

from typing import Final

# Transition matrix: from_status -> set of allowed to_statuses
ALLOWED_TRANSITIONS: Final[dict[str, set[str]]] = {
    "NEW": {"WARMING", "IDLE"},
    "WARMING": {"ACTIVE", "COOLDOWN", "NEEDS_ATTENTION", "IDLE"},
    "ACTIVE": {"COOLDOWN", "WARNING", "SHADOWBANNED", "NEEDS_ATTENTION", "BANNED", "IDLE"},
    "COOLDOWN": {"ACTIVE", "NEEDS_ATTENTION"},
    "WARNING": {"ACTIVE", "BANNED"},
    "NEEDS_ATTENTION": {"ACTIVE", "REMOVED"},
    "SHADOWBANNED": {"REMOVED", "IDLE"},
    "BANNED": {"REMOVED"},
    "IDLE": {"ACTIVE", "WARMING"},
    # REMOVED is terminal - no transitions out
    "REMOVED": set(),
}


def is_allowed(from_status: str, to_status: str) -> bool:
    """Check if a transition is allowed by the matrix."""
    return to_status in ALLOWED_TRANSITIONS.get(from_status, set())


def get_allowed_transitions(from_status: str) -> set[str]:
    """Get all allowed transitions from a given status."""
    return ALLOWED_TRANSITIONS.get(from_status, set()).copy()
