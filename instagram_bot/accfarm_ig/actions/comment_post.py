"""Comment post action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class CommentPostAction(Action):
    """Comment on posts."""

    name = "comment_post"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.commented = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.commented = 0

        comments_pool = params.get("comments_pool", [
            "Nice! 🔥",
            "Love this! ❤️",
            "Amazing 😍",
            "So cool!",
            "🔥🔥🔥",
            "Great content!",
        ])

        logger.info(
            f"Commenting on posts: max {max_count}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            import random
            while self.commented < max_count:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                # Find comment button
                try:
                    comment_btn = self.session.find(resourceId=ig_app.selectors.comment_button)
                    if not comment_btn.exists():
                        self.session.scroll_feed(direction="up")
                        self.session.sleep(1.0)
                        continue
                except Exception:
                    self.session.scroll_feed(direction="up")
                    self.session.sleep(1.0)
                    continue

                # Tap comment button
                self.session.tap_element(comment_btn)
                self.session.sleep(1.0)

                # Type comment (letter-by-letter)
                comment = random.choice(comments_pool)
                try:
                    comment_input = self.session.find(resourceId=ig_app.selectors.comment_input)
                    self.session.tap_element(comment_input)
                    self.session.sleep(0.5)
                    self.session.type_text(comment)
                    self.session.sleep(1.0)

                    # Post comment
                    post_btn = self.session.find(resourceId=ig_app.selectors.comment_post)
                    self.session.tap_element(post_btn)
                    self.commented += 1
                    
                    # Dwell to see it land
                    self.session.sleep(2.0 + time.time() % 2.0)
                except Exception as e:
                    logger.warning(f"Could not post comment: {e}")
                    self.session.press_back()

                self.session.sleep(1.5)

        except Exception as e:
            logger.error(f"Error commenting: {e}", exc_info=True)
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
            metadata={"commented": self.commented},
        )
