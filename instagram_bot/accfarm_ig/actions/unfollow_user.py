"""Unfollow user action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class UnfollowUserAction(Action):
    """Unfollow users."""

    name = "unfollow_user"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.unfollowed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.unfollowed = 0

        logger.info(
            f"Unfollowing users: max {max_count}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)
            
            # Navigate to our profile
            ig_app.navigate_to_profile()
            self.session.sleep(1.5)
            
            # Tap on following count to see who we follow
            try:
                following_elem = self.session.find(resourceId=ig_app.selectors.profile_following)
                if following_elem.exists():
                    self.session.tap_element(following_elem)
                    self.session.sleep(2.0)
            except Exception:
                logger.warning("Could not navigate to following list")
                return ActionResult(
                    success=False,
                    duration_ms=int((time.time() - start_time) * 1000),
                    action_name=self.name,
                    error="Could not access following list",
                )

            while self.unfollowed < max_count:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                # Find unfollow button (text-based)
                unfollow_btn = None
                for text in ig_app.selectors.unfollow_button_text:
                    try:
                        unfollow_btn = self.session.find(text=text)
                        if unfollow_btn.exists():
                            break
                    except Exception:
                        continue

                if not unfollow_btn or not unfollow_btn.exists():
                    # Scroll to find more
                    self.session.scroll_feed(direction="up")
                    self.session.sleep(1.0)
                    continue

                # Human delay
                self.session.sleep(2.0 + time.time() % 1.5)

                # Tap unfollow
                self.session.tap_element(unfollow_btn)
                self.unfollowed += 1
                
                # Confirm dialog might appear
                self.session.sleep(1.0)

        except Exception as e:
            logger.error(f"Error unfollowing users: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
                metadata={"unfollowed": self.unfollowed},
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={"unfollowed": self.unfollowed},
        )
