"""Instagram app lifecycle management."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from accfarm_ig.exceptions import NotLoggedInError, SelectorNotFoundError
from accfarm_ig.selectors.registry import get_selectors

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session

logger = logging.getLogger(__name__)


class InstagramApp:
    """Manages Instagram app lifecycle: open, login check, navigation."""

    def __init__(self, session: U2Session):
        self.session = session
        self._selectors = None
        self._ig_version: str | None = None

    @property
    def selectors(self):
        """Lazy-load selectors based on detected IG version."""
        if self._selectors is None:
            self._selectors = get_selectors(self._ig_version)
        return self._selectors

    def detect_version(self) -> str:
        """Detect Instagram version from the installed app."""
        # Get app info via uiautomator2
        try:
            app_info = self.session._u2.app_info(self.session.clone.package_name)
            version_name = app_info.get("versionName", "unknown")
            self._ig_version = version_name
            logger.info(
                f"Detected Instagram version: {version_name}",
                extra={"account_id": self.session.account_id},
            )
            return version_name
        except Exception as e:
            logger.warning(
                f"Could not detect IG version: {e}",
                extra={"account_id": self.session.account_id},
            )
            self._ig_version = "unknown"
            return "unknown"

    def open(self) -> None:
        """Open Instagram and ensure it's in foreground."""
        logger.info(
            "Opening Instagram",
            extra={"account_id": self.session.account_id},
        )
        self.session._u2.app_start(self.session.clone.package_name, stop=True)
        self.detect_version()

    def is_logged_in(self) -> bool:
        """Check if the account is logged in."""
        return self.session.is_logged_in()

    def assert_logged_in(self) -> None:
        """Raise NotLoggedInError if not logged in."""
        if not self.is_logged_in():
            raise NotLoggedInError(
                f"Account {self.session.account_id} is not logged in"
            )

    def navigate_to_home(self) -> None:
        """Navigate to the home tab."""
        logger.debug(
            "Navigating to home tab",
            extra={"account_id": self.session.account_id},
        )
        try:
            home_btn = self.session.find(resourceId=self.selectors.home_tab)
            self.session.tap_element(home_btn)
        except Exception as e:
            # Fallback: try text-based selector
            try:
                home_btn = self.session.find(text="Home")
                self.session.tap_element(home_btn)
            except Exception:
                logger.warning("Could not navigate to home tab", exc_info=True)

    def navigate_to_explore(self) -> None:
        """Navigate to the explore tab."""
        logger.debug(
            "Navigating to explore tab",
            extra={"account_id": self.session.account_id},
        )
        try:
            explore_btn = self.session.find(resourceId=self.selectors.explore_tab)
            self.session.tap_element(explore_btn)
        except Exception:
            logger.warning("Could not navigate to explore tab", exc_info=True)

    def navigate_to_profile(self, username: str | None = None) -> None:
        """Navigate to profile tab (own or specified user)."""
        logger.debug(
            f"Navigating to profile: {username or 'self'}",
            extra={"account_id": self.session.account_id},
        )
        try:
            profile_btn = self.session.find(resourceId=self.selectors.profile_tab)
            self.session.tap_element(profile_btn)
        except Exception:
            logger.warning("Could not navigate to profile tab", exc_info=True)

    def navigate_to_reels(self) -> None:
        """Navigate to the reels tab."""
        logger.debug(
            "Navigating to reels tab",
            extra={"account_id": self.session.account_id},
        )
        try:
            reels_btn = self.session.find(resourceId=self.selectors.reels_tab)
            self.session.tap_element(reels_btn)
        except Exception:
            logger.warning("Could not navigate to reels tab", exc_info=True)

    def go_back(self) -> None:
        """Press back button."""
        self.session.press_back()

    def go_home(self) -> None:
        """Press home button (exit to device home screen)."""
        self.session.press_home()

    def close(self) -> None:
        """Close Instagram gracefully (press home, don't force-stop)."""
        logger.info(
            "Closing Instagram",
            extra={"account_id": self.session.account_id},
        )
        self.go_home()
