"""U2Session - the high-level session object for bot layer interaction."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Literal

import numpy as np
import uiautomator2 as u2

from accfarm_device.exceptions import CloneNotForegroundError

if TYPE_CHECKING:
    from accfarm_device.clone import Clone
    from accfarm_device.device import Device
    from uuid import UUID

logger = logging.getLogger(__name__)


class UIElement:
    """Wrapper around uiautomator2 element with our timeouts."""

    def __init__(self, element, timeout: float = 10.0):
        self._element = element
        self._timeout = timeout

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Get element bounds (left, top, right, bottom)."""
        info = self._element.info
        return (
            info.get("bounds", {}).get("left", 0),
            info.get("bounds", {}).get("top", 0),
            info.get("bounds", {}).get("right", 0),
            info.get("bounds", {}).get("bottom", 0),
        )

    @property
    def center(self) -> tuple[int, int]:
        """Get center point of element."""
        left, top, right, bottom = self.bounds
        return ((left + right) // 2, (top + bottom) // 2)

    def click(self) -> None:
        """Click the element."""
        self._element.click()

    def exists(self) -> bool:
        """Check if element exists."""
        return self._element.exists(timeout=self._timeout)

    def wait(self, timeout: float | None = None) -> "UIElement":
        """Wait for element to appear."""
        self._element.wait(timeout=timeout or self._timeout)
        return self


class U2Session:
    """
    A live session bound to one clone on one phone.
    The bot layer calls into this and never below.
    """

    def __init__(
        self,
        u2_device: u2.Device,
        clone: Clone,
        device: Device,
        account_id: UUID,
    ):
        self._u2 = u2_device
        self.clone = clone
        self.device = device
        self.account_id = account_id

        # Ensure FastInputIME is active for typing
        self._u2.set_fastinput_ime(True)

    # ---- Element queries ----

    def find(self, **kwargs) -> UIElement:
        """Find an element with default timeout."""
        element = self._u2(**kwargs)
        return UIElement(element, timeout=10.0)

    def wait_for(self, timeout: float = 10.0, **kwargs) -> UIElement:
        """Wait for an element to appear and return it."""
        element = self._u2(**kwargs)
        element.wait(timeout=timeout)
        return UIElement(element, timeout=timeout)

    # ---- Humanized actions ----

    def tap(self, x: int, y: int, *, jitter_px: int = 8) -> None:
        """Tap with jitter so coordinates are never identical across runs."""
        from accfarm_device.humanize.tap import jittered_tap

        jittered_tap(self._u2, x, y, jitter_px=jitter_px)

    def tap_element(self, element: UIElement, *, jitter_px: int = 8) -> None:
        """Tap inside an element's bounding box, randomized."""
        from accfarm_device.humanize.tap import tap_in_rect

        left, top, right, bottom = element.bounds
        tap_in_rect(self._u2, left, top, right, bottom, jitter_px=jitter_px)

    def swipe(
        self,
        from_xy: tuple[int, int],
        to_xy: tuple[int, int],
        *,
        duration_ms_range: tuple[int, int] = (250, 600),
        curve: Literal["bezier", "linear"] = "bezier",
    ) -> None:
        """Bezier-curve swipe with humanized duration."""
        from accfarm_device.humanize.swipe import bezier_swipe

        bezier_swipe(
            self._u2,
            from_xy,
            to_xy,
            duration_ms_range=duration_ms_range,
            use_bezier=(curve == "bezier"),
        )

    def scroll_feed(
        self,
        direction: Literal["up", "down"] = "up",
        *,
        distance: float = 0.6,
    ) -> None:
        """Realistic feed scroll — slight diagonal, variable velocity."""
        display_width = self._u2.info["displayWidth"]
        display_height = self._u2.info["displayHeight"]

        # Start near bottom third, end near top third (or reverse for down)
        start_x = display_width // 2 + np.random.randint(-50, 50)
        if direction == "up":
            start_y = int(display_height * 0.7)
            end_y = int(display_height * 0.3)
        else:
            start_y = int(display_height * 0.3)
            end_y = int(display_height * 0.7)

        # Add slight diagonal offset
        end_x = start_x + np.random.randint(-30, 30)

        self.swipe(
            (start_x, start_y),
            (end_x, end_y),
            duration_ms_range=(300, 700),
            curve="bezier",
        )

    def type_text(
        self,
        text: str,
        *,
        wpm_range: tuple[int, int] = (40, 80),
        typo_rate: float = 0.04,
        use_suggestions: bool = True,
    ) -> None:
        """Type letter-by-letter at human speed with realistic patterns."""
        from accfarm_device.humanize.typing import human_type

        human_type(
            self._u2,
            text,
            wpm_range=wpm_range,
            typo_rate=typo_rate,
            use_suggestions=use_suggestions,
        )

    def sleep(self, mean_seconds: float, *, sigma: float = 0.3) -> None:
        """Log-normal sleep distribution. Min 50ms, no max."""
        from accfarm_device.humanize.timing import human_sleep

        human_sleep(mean_seconds, sigma=sigma)

    # ---- App control ----

    def press_back(self) -> None:
        """Press back button."""
        self._u2.press("back")

    def press_home(self) -> None:
        """Press home button."""
        self._u2.press("home")

    def press_app_switcher(self) -> None:
        """Press recent apps button."""
        self._u2.press("recent")

    # ---- Screen ----

    def screenshot(self) -> bytes:
        """Returns PNG bytes."""
        return self._u2.screenshot().tobytes()

    def dump_hierarchy(self) -> str:
        """XML hierarchy for debugging."""
        return self._u2.dump_hierarchy()

    # ---- Foreground guard ----

    def assert_foreground(self) -> None:
        """Raise CloneNotForegroundError if our clone is not the current foreground app."""
        if not self.clone.is_foreground(self.device):
            raise CloneNotForegroundError(
                f"Clone {self.clone.package_name} is not in foreground on device {self.device.serial}"
            )

    # ---- Health signals ----

    def is_logged_in(self) -> bool:
        """Look for the home tab vs the login screen."""
        try:
            # Check for home tab indicator (profile icon or home icon)
            return (
                self._u2(text="Home").exists(timeout=2)
                or self._u2(description="Home").exists(timeout=2)
                or self._u2(text="Profile").exists(timeout=2)
            )
        except Exception:
            return False

    def is_at_checkpoint(self) -> bool:
        """Detect verification screens, suspicious activity prompts."""
        checkpoint_indicators = [
            "suspicious",
            "verify",
            "verification",
            "checkpoint",
            "unusual activity",
            "try again later",
            "problem logging",
        ]

        try:
            # Get current screen text
            hierarchy = self.dump_hierarchy()
            hierarchy_lower = hierarchy.lower()

            for indicator in checkpoint_indicators:
                if indicator in hierarchy_lower:
                    logger.warning(
                        "Checkpoint detected",
                        extra={
                            "account_id": self.account_id,
                            "indicator": indicator,
                            "clone": self.clone.package_name,
                        },
                    )
                    return True

            return False
        except Exception:
            return False
