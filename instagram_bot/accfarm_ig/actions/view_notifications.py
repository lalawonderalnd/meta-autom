"""View notifications action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class ViewNotificationsAction(Action):
    """View the notifications tab."""

    name = "view_notifications"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.notifications_viewed = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.notifications_viewed = 0

        logger.info(
            "Viewing notifications",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Navigate to activity/notifications tab (heart icon)
            # This is typically accessed from home or profile
            
            # Scroll through notifications
            self.session.scroll_feed(direction="up")
            self.session.sleep(2.0 + time.time() % 2.0)
            self.notifications_viewed += 1

        except Exception as e:
            logger.error(f"Error viewing notifications: {e}", exc_info=True)
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
            metadata={"notifications_viewed": self.notifications_viewed},
        )
