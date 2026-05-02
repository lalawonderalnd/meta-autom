"""Bezier-curve swipe implementation for humanized automation."""

from __future__ import annotations

import random
import time
from typing import Literal


def quadratic_bezier(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    num_points: int = 40,
) -> list[tuple[float, float]]:
    """
    Generate points along a quadratic Bezier curve.

    Args:
        p0: Start point (x, y)
        p1: Control point (x, y)
        p2: End point (x, y)
        num_points: Number of points to sample

    Returns:
        List of (x, y) tuples along the curve
    """
    points = []
    for i in range(num_points):
        t = i / (num_points - 1)
        # Quadratic Bezier formula: B(t) = (1-t)²P0 + 2(1-t)tP1 + t²P2
        x = ((1 - t) ** 2) * p0[0] + 2 * (1 - t) * t * p1[0] + (t**2) * p2[0]
        y = ((1 - t) ** 2) * p0[1] + 2 * (1 - t) * t * p1[1] + (t**2) * p2[1]
        points.append((x, y))
    return points


def ease_in_out(t: float) -> float:
    """Ease-in-out function for variable velocity."""
    if t < 0.5:
        return 2 * t * t
    else:
        return 1 - ((-2 * t + 2) ** 2) / 2


def bezier_swipe(
    u2_device,
    from_xy: tuple[int, int],
    to_xy: tuple[int, int],
    *,
    duration_ms_range: tuple[int, int] = (250, 600),
    use_bezier: bool = True,
    perpendicular_offset_range: tuple[int, int] = (5, 25),
) -> None:
    """
    Perform a humanized swipe using Bezier curve with variable velocity.

    Args:
        u2_device: uiautomator2.Device instance
        from_xy: Start coordinates (x, y)
        to_xy: End coordinates (x, y)
        duration_ms_range: Range for random swipe duration in milliseconds
        use_bezier: Whether to use Bezier curve or linear path
        perpendicular_offset_range: Range for perpendicular offset of control point
    """
    import numpy as np

    x1, y1 = from_xy
    x2, y2 = to_xy

    # Calculate perpendicular offset for control point
    dx = x2 - x1
    dy = y2 - y1
    length = (dx**2 + dy**2) ** 0.5

    if length == 0:
        return

    # Unit perpendicular vector
    perp_x = -dy / length
    perp_y = dx / length

    # Random offset distance
    offset_distance = random.uniform(perpendicular_offset_range[0], perpendicular_offset_range[1])
    # Random direction (left or right of line)
    if random.random() > 0.5:
        offset_distance = -offset_distance

    # Control point is midpoint + perpendicular offset
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    control_point = (mid_x + perp_x * offset_distance, mid_y + perp_y * offset_distance)

    # Generate path points
    if use_bezier:
        path = quadratic_bezier(from_xy, control_point, to_xy, num_points=40)
    else:
        # Linear interpolation
        path = [
            (x1 + (x2 - x1) * i / 39, y1 + (y2 - y1) * i / 39)
            for i in range(40)
        ]

    # Random duration with ease-in-out velocity
    total_duration_ms = random.randint(duration_ms_range[0], duration_ms_range[1])

    # Use touch API for multi-step gesture
    touch = u2_device.touch

    # Start the touch
    touch.down(path[0][0], path[0][1])

    # Move along the path with variable velocity
    prev_t = 0.0
    for i, (px, py) in enumerate(path[1:], start=1):
        t = i / len(path)
        eased_t = ease_in_out(t)

        # Calculate delay based on velocity change
        delta_t = eased_t - prev_t
        delay_ms = delta_t * total_duration_ms
        prev_t = eased_t

        touch.move(px, py)
        time.sleep(delay_ms / 1000.0)

    # End the touch
    touch.up()


def generate_swipe_path(
    from_xy: tuple[int, int],
    to_xy: tuple[int, int],
    num_points: int = 40,
    perpendicular_offset_range: tuple[int, int] = (5, 25),
) -> list[tuple[float, float]]:
    """
    Generate a Bezier swipe path without executing it.
    Useful for testing and visualization.

    Returns:
        List of (x, y) points along the path
    """
    x1, y1 = from_xy
    x2, y2 = to_xy

    dx = x2 - x1
    dy = y2 - y1
    length = (dx**2 + dy**2) ** 0.5

    if length == 0:
        return [from_xy] * num_points

    perp_x = -dy / length
    perp_y = dx / length

    offset_distance = random.uniform(perpendicular_offset_range[0], perpendicular_offset_range[1])
    if random.random() > 0.5:
        offset_distance = -offset_distance

    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2
    control_point = (mid_x + perp_x * offset_distance, mid_y + perp_y * offset_distance)

    return quadratic_bezier(from_xy, control_point, to_xy, num_points=num_points)
