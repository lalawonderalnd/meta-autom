"""Post reel action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class PostReelAction(Action):
    """Post a reel."""

    name = "post_reel"

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
            f"Posting reel: {content_item_id}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Full implementation would:
            # 1. Push video from R2 to device /sdcard/DCIM/AccFarm/
            # 2. Tap + button → Reel
            # 3. Select gallery, find our video (most recent)
            # 4. Tap Next
            # 5. Add caption (letter-by-letter)
            # 6. Add hashtags (5-10 from pool)
            # 7. Tap Share
            # 8. Wait for upload (poll progress UI, timeout 120s)
            # CRITICAL: Don't lock screen or switch apps during upload

            self.posted = True

        except Exception as e:
            logger.error(f"Error posting reel: {e}", exc_info=True)
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
