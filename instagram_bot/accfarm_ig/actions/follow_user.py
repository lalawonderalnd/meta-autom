"""Follow user action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class FollowUserAction(Action):
    """Follow users with human-like behavior."""

    name = "follow_user"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.followed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.followed = 0

        daily_cap = self.daily_cap_remaining or max_count

        logger.info(
            f"Following users: max {max_count}, daily cap: {daily_cap}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            while self.followed < max_count and self.followed < daily_cap:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                # Find follow button (text-based since it varies by language)
                follow_btn = None
                for text in ig_app.selectors.follow_button_text:
                    try:
                        follow_btn = self.session.find(text=text)
                        if follow_btn.exists():
                            break
                    except Exception:
                        continue

                if not follow_btn or not follow_btn.exists():
                    logger.debug("No follow button found, scrolling")
                    self.session.scroll_feed(direction="up")
                    self.session.sleep(1.0)
                    continue

                # Human delay before following
                self.session.sleep(2.0 + time.time() % 1.5)

                # Tap follow
                self.session.tap_element(follow_btn)
                self.followed += 1
                logger.debug(f"Followed user #{self.followed}")

                # Pause after following
                self.session.sleep(1.5 + time.time() % 1.0)

                # Check for warnings
                if self.followed % 3 == 0:
                    warning = self._check_for_warnings()
                    if warning:
                        return ActionResult(
                            success=True,
                            duration_ms=int((time.time() - start_time) * 1000),
                            action_name=self.name,
                            metadata={"followed": self.followed},
                            warning=warning,
                        )

                # Move to next potential follow
                self.session.scroll_feed(direction="up")
                self.session.sleep(1.0)

        except Exception as e:
            logger.error(f"Error following users: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
                metadata={"followed": self.followed},
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={"followed": self.followed},
        )
