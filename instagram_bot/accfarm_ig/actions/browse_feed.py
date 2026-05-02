"""Browse feed action - scroll through the home feed."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult
from accfarm_ig.humanize_extras.reading_time import post_dwell_time
from accfarm_ig.humanize_extras.distraction import maybe_scroll_back

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class BrowseFeedAction(Action):
    """Scroll through the home feed with human-like behavior."""

    name = "browse_feed"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.posts_viewed = 0
        self.scrolls_performed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        """
        Browse the home feed.

        Args:
            params: Optional params like {"min_posts": N}
            max_count: Maximum number of posts to view (default: 20)
            max_duration: Maximum duration in seconds

        Returns:
            ActionResult with metadata about posts viewed and scrolls
        """
        start_time = time.time()
        self.posts_viewed = 0
        self.scrolls_performed = 0

        target_posts = min(max_count, params.get("max_posts", 20))
        min_posts = params.get("min_posts", 5)

        logger.info(
            f"Browsing feed: target {target_posts} posts",
            extra={"account_id": self.account.id},
        )

        try:
            # Ensure we're on home tab
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)
            ig_app.navigate_to_home()
            self.session.sleep(1.0)

            # Find the feed recycler
            feed = self.session.find(resourceId=ig_app.selectors.feed_recycler)

            while True:
                # Check duration limit
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    logger.info(f"Reached max duration ({max_duration}s)")
                    break

                # Check if we've viewed enough posts
                if self.posts_viewed >= target_posts:
                    break

                # Scroll down (up on screen = more content)
                self.session.scroll_feed(direction="up")
                self.scrolls_performed += 1
                self.posts_viewed += 1

                # Dwell on this post based on simulated content
                dwell = post_dwell_time(
                    has_caption=True,
                    caption_length=150,  # Average
                    is_video=False,
                    video_duration=0,
                )
                self.session.sleep(dwell)

                # Occasionally scroll back up (3% chance)
                if maybe_scroll_back():
                    self.session.scroll_feed(direction="down")
                    self.session.sleep(0.8)

                # Check for warnings periodically
                if self.posts_viewed % 5 == 0:
                    warning = self._check_for_warnings()
                    if warning:
                        return ActionResult(
                            success=True,
                            duration_ms=int((time.time() - start_time) * 1000),
                            action_name=self.name,
                            metadata={
                                "posts_viewed": self.posts_viewed,
                                "scrolls": self.scrolls_performed,
                            },
                            warning=warning,
                        )

        except Exception as e:
            logger.error(f"Error browsing feed: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
                metadata={
                    "posts_viewed": self.posts_viewed,
                    "scrolls": self.scrolls_performed,
                },
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={
                "posts_viewed": self.posts_viewed,
                "scrolls": self.scrolls_performed,
            },
        )
