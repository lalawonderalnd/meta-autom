"""Sleep timing utilities for humanized automation."""

from __future__ import annotations

import random
import time
from typing import Literal


def human_sleep(mean_seconds: float, *, sigma: float = 0.3, min_seconds: float = 0.05) -> None:
    """
    Sleep for a log-normally distributed duration.

    Args:
        mean_seconds: Mean of the distribution (before log transform)
        sigma: Standard deviation of the log-normal distribution
        min_seconds: Minimum sleep duration
    """
    import numpy as np

    duration = np.random.lognormal(np.log(mean_seconds), sigma)
    duration = max(min_seconds, duration)
    time.sleep(duration)


def between_actions_sleep(action_kind: Literal["tap", "scroll", "type", "swipe", "navigate"]) -> float:
    """
    Get an appropriate sleep duration between actions based on action type.

    Returns:
        Sleep duration in seconds (caller should call time.sleep())
    """
    import numpy as np

    # Different distributions for different action types
    distributions = {
        "tap": {"mean": 0.3, "sigma": 0.4},      # Quick pause after tap
        "scroll": {"mean": 0.8, "sigma": 0.5},   # Longer pause to read content
        "type": {"mean": 0.5, "sigma": 0.4},     # Pause after typing
        "swipe": {"mean": 0.6, "sigma": 0.4},    # Pause after swipe
        "navigate": {"mean": 1.5, "sigma": 0.6}, # Longer pause after navigation
    }

    params = distributions.get(action_kind, {"mean": 0.5, "sigma": 0.4})
    duration = np.random.lognormal(np.log(params["mean"]), params["sigma"])
    return max(0.05, min(duration, 5.0))


class SleepContext:
    """Context manager for natural-looking action sequences."""

    def __init__(self, action_kind: Literal["tap", "scroll", "type", "swipe", "navigate"] = "tap"):
        self.action_kind = action_kind
        self._duration: float = 0.0

    def __enter__(self) -> "SleepContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:  # Only sleep if no exception
            self._duration = between_actions_sleep(self.action_kind)
            time.sleep(self._duration)

    @property
    def duration(self) -> float:
        """Get the actual sleep duration that was used."""
        return self._duration


def random_pause(
    min_seconds: float = 0.2,
    max_seconds: float = 2.0,
    distribution: Literal["uniform", "lognormal"] = "lognormal",
) -> float:
    """
    Take a random pause within specified bounds.

    Args:
        min_seconds: Minimum pause duration
        max_seconds: Maximum pause duration
        distribution: Type of distribution to use

    Returns:
        Actual pause duration in seconds
    """
    import numpy as np

    if distribution == "uniform":
        duration = random.uniform(min_seconds, max_seconds)
    else:
        # Log-normal centered in the range
        mean = (min_seconds + max_seconds) / 2
        sigma = 0.5
        duration = np.random.lognormal(np.log(mean), sigma)
        duration = max(min_seconds, min(duration, max_seconds))

    time.sleep(duration)
    return duration
