"""Optimal posting times per niche."""

import random
from datetime import datetime, time, timezone
from typing import Final

# Per-niche peak windows in the account's local timezone
# Format: (start_hour, end_hour) - inclusive start, exclusive end
POSTING_WINDOWS: Final[dict[str, list[tuple[int, int]]]] = {
    "fitness": [(6, 8), (12, 13), (18, 20)],
    "alt": [(15, 17), (20, 23)],
    "cosplay": [(14, 18), (21, 23)],
    "default": [(9, 11), (14, 16), (19, 21)],
}

# Country to timezone mapping (simplified - use pytz or zoneinfo in production)
COUNTRY_TIMEZONES: Final[dict[str, str]] = {
    "US": "America/New_York",
    "GB": "Europe/London",
    "DE": "Europe/Berlin",
    "FR": "Europe/Paris",
    "BR": "America/Sao_Paulo",
    "IN": "Asia/Kolkata",
    "AU": "Australia/Sydney",
    "CA": "America/Toronto",
    "MX": "America/Mexico_City",
    "JP": "Asia/Tokyo",
}


def get_posting_window(niche: str | None = None) -> list[tuple[int, int]]:
    """Get the posting windows for a given niche."""
    return POSTING_WINDOWS.get(niche, POSTING_WINDOWS["default"])


def sample_posting_time(
    niche: str | None = None,
    earliest: datetime | None = None,
) -> datetime:
    """
    Sample a posting time within the next applicable window.

    Uses a Gaussian distribution centered on the window midpoint.

    Args:
        niche: The account's niche
        earliest: The earliest allowed time (defaults to now)

    Returns:
        A datetime for the scheduled post
    """
    if earliest is None:
        earliest = datetime.now(timezone.utc)

    windows = get_posting_window(niche)
    now = earliest

    # Find the next applicable window
    current_hour = now.hour

    for start, end in windows:
        if start <= current_hour < end:
            # We're in a window - schedule within this window with some randomness
            midpoint = (start + end) / 2
            break
    else:
        # Not in any window - find the next one
        for start, end in windows:
            if start > current_hour:
                midpoint = (start + end) / 2
                break
        else:
            # All windows passed today - use first window tomorrow
            start, end = windows[0]
            midpoint = (start + end) / 2
            # Add a day
            from datetime import timedelta
            now = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # Sample from Gaussian centered on midpoint with std dev of 1 hour
    sampled_hour = int(random.gauss(midpoint, 1))
    sampled_hour = max(0, min(23, sampled_hour))  # Clamp to valid range
    sampled_minute = random.randint(0, 59)

    return now.replace(hour=sampled_hour, minute=sampled_minute, second=0, microsecond=0)


def get_timezone_for_country(country_code: str) -> str:
    """Get the timezone for a country code."""
    return COUNTRY_TIMEZONES.get(country_code, "UTC")
