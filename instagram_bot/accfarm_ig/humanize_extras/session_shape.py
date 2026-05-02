"""Session attention curve sampling."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Literal


@dataclass
class AttentionCurve:
    """Defines how attentive the session will be."""

    level: Literal["high", "medium", "low"]
    # Multipliers for various behaviors
    dwell_multiplier: float
    read_captions: bool
    watch_stories_fully: bool
    interact_rate: float  # 0.0 to 1.0


def sample_attention_curve() -> AttentionCurve:
    """
    Sample an attention curve for the session.

    Distribution:
    - 30% high-attention: careful browsing, captions read, profiles browsed
    - 50% medium-attention: skim through, basic interactions
    - 20% low-attention: minimal — just open, scroll a bit, close

    Returns:
        AttentionCurve instance
    """
    rand = random.random()
    
    if rand < 0.30:
        # High attention session
        return AttentionCurve(
            level="high",
            dwell_multiplier=random.uniform(1.2, 1.8),
            read_captions=True,
            watch_stories_fully=True,
            interact_rate=random.uniform(0.6, 0.9),
        )
    elif rand < 0.80:  # 0.30 + 0.50
        # Medium attention session
        return AttentionCurve(
            level="medium",
            dwell_multiplier=random.uniform(0.8, 1.2),
            read_captions=random.random() < 0.5,
            watch_stories_fully=random.random() < 0.7,
            interact_rate=random.uniform(0.3, 0.6),
        )
    else:
        # Low attention session
        return AttentionCurve(
            level="low",
            dwell_multiplier=random.uniform(0.4, 0.8),
            read_captions=False,
            watch_stories_fully=False,
            interact_rate=random.uniform(0.1, 0.3),
        )


def apply_attention_curve(
    base_duration: float, curve: AttentionCurve
) -> float:
    """
    Apply attention curve multiplier to a duration.

    Args:
        base_duration: Base duration in seconds
        curve: The sampled attention curve

    Returns:
        Adjusted duration in seconds
    """
    return base_duration * curve.dwell_multiplier
