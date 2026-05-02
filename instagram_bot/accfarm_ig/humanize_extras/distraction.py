"""Occasional 'lost focus' behaviors for realism."""

from __future__ import annotations

import random


def maybe_scroll_back() -> bool:
    """
    Decide if user should scroll back up (re-read previous post).

    Real users occasionally scroll back up to re-read something.
    Pure forward-scroll bots lack this pattern.

    Returns:
        True if should scroll back (3% chance)
    """
    return random.random() < 0.03


def maybe_distraction() -> tuple[bool, str]:
    """
    Decide if a distraction behavior should occur.

    Distractions mimic real user "lost focus" patterns:
    - Tap a notification badge, look at it, back out (5%)
    - Tap into search, type a few letters, navigate back (8%)
    - Random tap-and-back-out (3%)

    Returns:
        Tuple of (should_distract, distraction_type)
        distraction_type: "notification", "search", "random_tap", or ""
    """
    rand = random.random()
    
    if rand < 0.05:
        return True, "notification"
    elif rand < 0.13:  # 0.05 + 0.08
        return True, "search"
    elif rand < 0.16:  # 0.13 + 0.03
        return True, "random_tap"
    
    return False, ""


def distraction_params(distraction_type: str) -> dict:
    """
    Get parameters for executing a distraction behavior.

    Args:
        distraction_type: One of "notification", "search", "random_tap"

    Returns:
        Dict with parameters for the distraction
    """
    if distraction_type == "notification":
        return {
            "dwell_seconds": random.uniform(2.0, 5.0),
            "tap_count": random.randint(1, 3),
        }
    elif distraction_type == "search":
        return {
            "chars_to_type": random.randint(2, 5),
            "dwell_seconds": random.uniform(1.5, 4.0),
        }
    elif distraction_type == "random_tap":
        return {
            "dwell_seconds": random.uniform(0.5, 2.0),
        }
    
    return {}
