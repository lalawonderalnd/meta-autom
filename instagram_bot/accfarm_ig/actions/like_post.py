"""Like post action - double-tap or tap heart to like posts."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class LikePostAction(Action):
    """Like posts with human-like behavior (double-tap or heart icon)."""

    name = "like_post"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.liked = 0
        self.skipped = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        """
        Like posts in the current feed/context.

        Args:
            params: Optional params like {"double_tap_rate": 0.7}
            max_count: Maximum number of posts to like
            max_duration: Maximum duration in seconds

        Returns:
            ActionResult with metadata about likes performed
        """
        start_time = time.time()
        self.liked = 0
        self.skipped = 0

        double_tap_rate = params.get("double_tap_rate", 0.7)

        # Get daily cap from runner context if available
        daily_cap = self.daily_cap_remaining or max_count

        logger.info(
            f"Liking posts: max {max_count}, daily cap remaining: {daily_cap}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            attempts = 0
            max_attempts = max_count * 3  # Allow for skipped posts

            while self.liked < max_count and self.liked < daily_cap and attempts < max_attempts:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                attempts += 1

                # Check for warnings every 3 likes
                if self.liked > 0 and self.liked % 3 == 0:
                    warning = self._check_for_warnings()
                    if warning:
                        return ActionResult(
                            success=True,
                            duration_ms=int((time.time() - start_time) * 1000),
                            action_name=self.name,
                            metadata={"liked": self.liked, "skipped": self.skipped},
                            warning=warning,
                        )

                # Find the current post's like button
                try:
                    like_btn = self.session.find(resourceId=ig_app.selectors.like_button)
                    if not like_btn.exists():
                        # Try to scroll to find more posts
                        self.session.scroll_feed(direction="up")
                        self.session.sleep(1.0)
                        continue
                except Exception:
                    logger.debug("Could not find like button, scrolling")
                    self.session.scroll_feed(direction="up")
                    self.session.sleep(1.0)
                    continue

                # Human-like dwell time before liking
                self.session.sleep(1.5 + time.time() % 2.0)

                # Double-tap (70%) or tap heart icon (30%)
                import random
                if random.random() < double_tap_rate:
                    # Double-tap the post image (more human)
                    self._double_tap_post()
                    logger.debug("Double-tapped to like")
                else:
                    # Tap the heart icon
                    self.session.tap_element(like_btn)
                    logger.debug("Tapped heart icon to like")

                self.liked += 1

                # Small pause after liking
                self.session.sleep(0.8 + time.time() % 0.5)

                # Scroll to next post
                self.session.scroll_feed(direction="up")
                self.session.sleep(1.0)

        except Exception as e:
            logger.error(f"Error liking posts: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
                metadata={"liked": self.liked, "skipped": self.skipped},
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={"liked": self.liked, "skipped": self.skipped},
        )

    def _double_tap_post(self) -> None:
        """Double-tap in the center area of the screen to like a post."""
        display_width = self.session._u2.info["displayWidth"]
        display_height = self.session._u2.info["displayHeight"]

        # Tap in the center area of the screen (where the post image is)
        center_x = display_width // 2
        center_y = display_height // 2

        # Add some jitter so taps aren't identical
        import random
        jitter_x = random.randint(-50, 50)
        jitter_y = random.randint(-50, 50)

        # First tap
        self.session.tap(center_x + jitter_x, center_y + jitter_y)
        self.session.sleep(0.15)  # 150ms between taps

        # Second tap (slightly different position)
        jitter_x2 = random.randint(-50, 50)
        jitter_y2 = random.randint(-50, 50)
        self.session.tap(center_x + jitter_x2, center_y + jitter_y2)
