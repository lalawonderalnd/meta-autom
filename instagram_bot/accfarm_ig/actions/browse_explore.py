"""Browse explore action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class BrowseExploreAction(Action):
    """Browse the explore page."""

    name = "browse_explore"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.posts_viewed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.posts_viewed = 0

        logger.info(
            "Browsing explore page",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Navigate to explore
            ig_app.navigate_to_explore()
            self.session.sleep(1.5)

            # Browse the explore grid
            while self.posts_viewed < max_count:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                self.session.scroll_feed(direction="up")
                self.session.sleep(1.5 + time.time() % 2.0)
                self.posts_viewed += 1

                # Occasionally tap on a post to view it
                if time.time() % 5 < 1.5:
                    self._view_post()

        except Exception as e:
            logger.error(f"Error browsing explore: {e}", exc_info=True)
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
            metadata={"posts_viewed": self.posts_viewed},
        )

    def _view_post(self) -> None:
        """Tap to view a post in detail."""
        display_width = self.session._u2.info["displayWidth"]
        display_height = self.session._u2.info["displayHeight"]
        
        # Tap in the center area
        self.session.tap(display_width // 2, display_height // 3)
        self.session.sleep(2.0 + time.time() % 3.0)
        self.session.press_back()
        self.session.sleep(0.5)
