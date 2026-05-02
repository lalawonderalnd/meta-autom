"""Realistic post dwell time based on content."""

from __future__ import annotations

import math
import random


def post_dwell_time(
    has_caption: bool = True,
    caption_length: int = 150,
    is_video: bool = False,
    video_duration: float = 0.0,
) -> float:
    """
    Calculate realistic dwell time for a post.

    Based on research showing real users:
    - Spend 2-4 seconds on average posts
    - Read captions proportionally (about 200 chars per 8 seconds max)
    - Watch ~40% of video content on average

    Args:
        has_caption: Whether the post has a caption
        caption_length: Length of caption in characters
        is_video: Whether this is a video/reel
        video_duration: Duration of video in seconds

    Returns:
        Dwell time in seconds (float)
    """
    # Base dwell time with log-normal distribution for natural variation
    base = random.lognormvariate(0.9, 0.4)  # Mean ~2.5s, sigma 0.6
    
    # Add time for caption reading
    if has_caption and caption_length > 0:
        # About 200 characters per 8 seconds max reading time
        caption_time = min(caption_length / 200 * 8, 8.0)
        # Not everyone reads the full caption - add 30-70% of potential reading time
        base += caption_time * random.uniform(0.3, 0.7)
    
    # Add time for video watching
    if is_video and video_duration > 0:
        # Real users watch ~40% of videos on average, but it varies widely
        watch_ratio = random.uniform(0.2, 0.6)
        video_time = min(video_duration * watch_ratio, 12.0)  # Cap at 12s extra
        base += video_time
    
    # Add small random variation
    base += random.uniform(-0.3, 0.5)
    
    # Ensure minimum dwell time
    return max(base, 1.0)


def caption_read_depth(caption_length: int) -> float:
    """
    Estimate how much of a caption a user would read.

    Returns:
        Ratio of caption likely read (0.0 to 1.0)
    """
    if caption_length <= 50:
        return random.uniform(0.8, 1.0)
    elif caption_length <= 200:
        return random.uniform(0.5, 0.9)
    else:
        # Long captions - many users skim or skip
        return random.uniform(0.2, 0.6)
