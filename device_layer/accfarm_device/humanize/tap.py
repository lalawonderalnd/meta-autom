"""Jittered tap implementation for humanized automation."""

from __future__ import annotations

import random


def jittered_tap(
    u2_device,
    x: int,
    y: int,
    *,
    jitter_px: int = 8,
    miss_rate: float = 0.05,
    miss_offset_range: tuple[int, int] = (1, 3),
) -> None:
    """
    Tap with jitter so coordinates are never identical across runs.

    Args:
        u2_device: uiautomator2.Device instance
        x: Target x coordinate
        y: Target y coordinate
        jitter_px: Standard deviation of jitter in pixels
        miss_rate: Probability of a "missed" tap outside target
        miss_offset_range: Range for miss offset in pixels
    """
    import numpy as np

    # Sample from 2D Gaussian centered at target
    jitter_x = np.random.normal(0, jitter_px)
    jitter_y = np.random.normal(0, jitter_px)

    tap_x = int(x + jitter_x)
    tap_y = int(y + jitter_y)

    # Occasionally do a "missed" tap followed by corrective tap
    if random.random() < miss_rate:
        # First tap slightly outside
        miss_direction = random.choice([-1, 1])
        miss_x_offset = random.randint(miss_offset_range[0], miss_offset_range[1]) * miss_direction
        miss_y_offset = random.randint(miss_offset_range[0], miss_offset_range[1]) * random.choice([-1, 1])

        u2_device.click(tap_x + miss_x_offset, tap_y + miss_y_offset)
        u2_device.sleep(0.1)  # Brief pause before correction

        # Corrective tap
        u2_device.click(tap_x, tap_y)
    else:
        u2_device.click(tap_x, tap_y)


def tap_in_rect(
    u2_device,
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    jitter_px: int = 8,
    center_offset_std: float = 0.25,
    miss_rate: float = 0.05,
) -> None:
    """
    Tap inside a rectangle with randomized position.

    Args:
        u2_device: uiautomator2.Device instance
        left: Left bound of target rect
        top: Top bound of target rect
        right: Right bound of target rect
        bottom: Bottom bound of target rect
        jitter_px: Additional jitter after sampling within rect
        center_offset_std: Standard deviation as fraction of rect size for center offset
        miss_rate: Probability of a "missed" tap outside rect
    """
    import numpy as np

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        return

    # Center of the rect
    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    # Sample from 2D Gaussian centered slightly off-center
    std_x = width * center_offset_std
    std_y = height * center_offset_std

    offset_x = np.random.normal(0, std_x)
    offset_y = np.random.normal(0, std_y)

    # Clamp to within rect bounds
    tap_x = int(np.clip(center_x + offset_x, left, right))
    tap_y = int(np.clip(center_y + offset_y, top, bottom))

    # Add additional small jitter
    tap_x += int(np.random.normal(0, jitter_px))
    tap_y += int(np.random.normal(0, jitter_px))

    # Clamp again after jitter
    tap_x = int(np.clip(tap_x, left, right))
    tap_y = int(np.clip(tap_y, top, bottom))

    # Occasionally do a "missed" tap followed by corrective tap
    if random.random() < miss_rate:
        # First tap slightly outside
        if random.random() > 0.5:
            # Miss horizontally
            if random.random() > 0.5:
                miss_x = right + random.randint(1, 3)
            else:
                miss_x = left - random.randint(1, 3)
            miss_y = tap_y
        else:
            # Miss vertically
            miss_x = tap_x
            if random.random() > 0.5:
                miss_y = bottom + random.randint(1, 3)
            else:
                miss_y = top - random.randint(1, 3)

        u2_device.click(miss_x, miss_y)
        u2_device.sleep(0.1)

        # Corrective tap inside
        u2_device.click(tap_x, tap_y)
    else:
        u2_device.click(tap_x, tap_y)


def generate_tap_position(
    left: int,
    top: int,
    right: int,
    bottom: int,
    *,
    jitter_px: int = 8,
    center_offset_std: float = 0.25,
) -> tuple[int, int]:
    """
    Generate a randomized tap position within a rectangle.
    Useful for testing without executing the tap.

    Returns:
        (x, y) tuple of tap coordinates
    """
    import numpy as np

    width = right - left
    height = bottom - top

    if width <= 0 or height <= 0:
        return (left, top)

    center_x = (left + right) / 2
    center_y = (top + bottom) / 2

    std_x = width * center_offset_std
    std_y = height * center_offset_std

    offset_x = np.random.normal(0, std_x)
    offset_y = np.random.normal(0, std_y)

    tap_x = int(np.clip(center_x + offset_x, left, right))
    tap_y = int(np.clip(center_y + offset_y, top, bottom))

    tap_x += int(np.random.normal(0, jitter_px))
    tap_y += int(np.random.normal(0, jitter_px))

    tap_x = int(np.clip(tap_x, left, right))
    tap_y = int(np.clip(tap_y, top, bottom))

    return (tap_x, tap_y)
