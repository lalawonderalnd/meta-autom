"""Browse profile action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class BrowseProfileAction(Action):
    """Browse a user's profile."""

    name = "browse_profile"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.profiles_viewed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.profiles_viewed = 0

        username = params.get("username")

        logger.info(
            f"Browsing profile: {username or 'from context'}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # If username provided, search for it
            if username:
                self._search_username(username)
                self.session.sleep(1.5)

            # Browse the profile grid
            self.session.scroll_feed(direction="up")
            self.session.sleep(2.0 + time.time() % 2.0)
            self.profiles_viewed += 1

        except Exception as e:
            logger.error(f"Error browsing profile: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={"profiles_viewed": self.profiles_viewed},
        )

    def _search_username(self, username: str) -> None:
        """Search for a username."""
        from accfarm_ig.ig_app import InstagramApp
        ig_app = InstagramApp(self.session)
        
        # Navigate to explore/search
        ig_app.navigate_to_explore()
        self.session.sleep(1.0)
        
        # Tap search input
        try:
            search_input = self.session.find(resourceId=ig_app.selectors.search_input)
            self.session.tap_element(search_input)
            self.session.sleep(0.5)
            
            # Type the username
            self.session.type_text(username)
            self.session.sleep(1.5)
            
            # Tap on the first result
            self.session.press_back()  # Close keyboard
            self.session.sleep(0.5)
        except Exception:
            logger.warning("Could not search for username")
