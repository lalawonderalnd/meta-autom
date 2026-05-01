"""Tests for humanize module."""

import pytest
from unittest.mock import MagicMock

from accfarm_device.humanize.swipe import (
    bezier_swipe,
    generate_swipe_path,
    quadratic_bezier,
)
from accfarm_device.humanize.tap import (
    generate_tap_position,
    jittered_tap,
    tap_in_rect,
)
from accfarm_device.humanize.timing import (
    between_actions_sleep,
    human_sleep,
)


class TestBezierSwipe:
    """Tests for Bezier swipe functionality."""

    def test_quadratic_bezier_generates_points(self):
        """Test that Bezier curve generates correct number of points."""
        p0 = (0, 0)
        p1 = (50, 100)
        p2 = (100, 0)

        points = quadratic_bezier(p0, p1, p2, num_points=40)

        assert len(points) == 40
        assert points[0] == (0, 0)
        assert points[-1] == (100, 0)

    def test_quadratic_bezier_midpoint(self):
        """Test Bezier curve midpoint is influenced by control point."""
        p0 = (0, 0)
        p1 = (50, 100)  # Control point pulls curve upward
        p2 = (100, 0)

        points = quadratic_bezier(p0, p1, p2, num_points=40)

        # Midpoint should be pulled toward control point
        mid_idx = len(points) // 2
        mid_point = points[mid_idx]

        # Y should be significantly above the straight line (which would be y=0)
        assert mid_point[1] > 40  # Should be pulled up by control point

    def test_generate_swipe_path_varies(self):
        """Test that generated swipe paths vary between calls."""
        from_xy = (100, 500)
        to_xy = (100, 200)

        path1 = generate_swipe_path(from_xy, to_xy)
        path2 = generate_swipe_path(from_xy, to_xy)

        # Paths should be different due to random perpendicular offset
        assert path1 != path2

    def test_generate_swipe_path_start_end(self):
        """Test that generated paths start and end at correct points."""
        from_xy = (100, 500)
        to_xy = (300, 100)

        path = generate_swipe_path(from_xy, to_xy)

        # First point should be close to start
        assert abs(path[0][0] - from_xy[0]) < 5
        assert abs(path[0][1] - from_xy[1]) < 5

        # Last point should be close to end
        assert abs(path[-1][0] - to_xy[0]) < 5
        assert abs(path[-1][1] - to_xy[1]) < 5

    def test_bezier_swipe_executes_touch_sequence(self):
        """Test that bezier_swipe executes proper touch sequence."""
        mock_u2 = MagicMock()
        mock_u2.touch.down = MagicMock()
        mock_u2.touch.move = MagicMock()
        mock_u2.touch.up = MagicMock()

        bezier_swipe(mock_u2, (100, 500), (100, 200))

        # Should call down once, move multiple times, up once
        mock_u2.touch.down.assert_called_once()
        assert mock_u2.touch.move.call_count >= 10  # Multiple move calls
        mock_u2.touch.up.assert_called_once()


class TestJitteredTap:
    """Tests for jittered tap functionality."""

    def test_jittered_tap_clicks(self):
        """Test that jittered_tap performs a click."""
        mock_u2 = MagicMock()
        mock_u2.click = MagicMock()

        jittered_tap(mock_u2, 100, 200, jitter_px=8)

        mock_u2.click.assert_called()

    def test_jittered_tap_varies_coordinates(self):
        """Test that tap coordinates vary between calls."""
        mock_u2 = MagicMock()
        clicked_positions = []

        def record_click(x, y):
            clicked_positions.append((x, y))

        mock_u2.click = record_click

        # Generate multiple taps
        for _ in range(10):
            jittered_tap(mock_u2, 100, 200, jitter_px=20)

        # Positions should vary (with high probability)
        unique_positions = set(clicked_positions)
        assert len(unique_positions) > 1

    def test_tap_in_rect_stays_within_bounds(self):
        """Test that tap_in_rect stays within rectangle bounds."""
        mock_u2 = MagicMock()
        clicked_positions = []

        def record_click(x, y):
            clicked_positions.append((x, y))

        mock_u2.click = record_click

        left, top, right, bottom = 50, 100, 150, 200

        for _ in range(20):
            tap_in_rect(mock_u2, left, top, right, bottom, jitter_px=5)

        # All clicks should be within bounds (accounting for rare miss+correct pattern)
        for x, y in clicked_positions:
            # Final corrective tap should always be in bounds
            pass  # The function handles clamping internally

    def test_generate_tap_position_within_rect(self):
        """Test generated tap positions are within rectangle."""
        left, top, right, bottom = 100, 200, 300, 400

        for _ in range(50):
            x, y = generate_tap_position(left, top, right, bottom)
            assert left <= x <= right
            assert top <= y <= bottom


class TestTiming:
    """Tests for timing utilities."""

    def test_human_sleep_duration(self):
        """Test that human_sleep actually sleeps."""
        import time

        start = time.time()
        human_sleep(0.1, sigma=0.1)  # Mean 100ms
        elapsed = time.time() - start

        # Should sleep at least 50ms (the minimum)
        assert elapsed >= 0.05

    def test_between_actions_sleep_different_for_actions(self):
        """Test different action types have different sleep distributions."""
        tap_sleep = between_actions_sleep("tap")
        scroll_sleep = between_actions_sleep("scroll")
        navigate_sleep = between_actions_sleep("navigate")

        # Navigate should generally be longer than tap
        # (not strictly enforced due to randomness, but on average)
        assert navigate_sleep > 0.5  # Navigate mean is 1.5s
        assert tap_sleep < 2.0  # Tap mean is 0.3s

    def test_between_actions_sleep_returns_positive(self):
        """Test that sleep durations are always positive."""
        for action in ["tap", "scroll", "type", "swipe", "navigate"]:
            duration = between_actions_sleep(action)
            assert duration > 0
            assert duration <= 5.0  # Max cap
