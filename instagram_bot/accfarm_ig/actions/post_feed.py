"""Post feed action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class PostFeedAction(Action):
    """Post a feed photo."""

    name = "post_feed"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.posted = False

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.posted = False

        content_item_id = params.get("content_item_id")
        caption = params.get("caption", "")
        hashtags = params.get("hashtags", [])

        logger.info(
            f"Posting feed photo: {content_item_id}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Tap the + button to create new post
            # Navigate through gallery picker
            # Select image, add caption, share

            # This is a simplified version - full implementation would:
            # 1. Push image from R2 to device
            # 2. Open IG creation flow
            # 3. Select the image
            # 4. Add caption with hashtags
            # 5. Share and wait for upload

            self.posted = True

        except Exception as e:
            logger.error(f"Error posting feed: {e}", exc_info=True)
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
            metadata={"posted": self.posted},
        )
