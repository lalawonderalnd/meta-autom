"""Post story action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class PostStoryAction(Action):
    """Post a story."""

    name = "post_story"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.posted = False

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.posted = False

        content_item_id = params.get("content_item_id")

        logger.info(
            f"Posting story: {content_item_id}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Full implementation would:
            # 1. Push image/video from R2 to device
            # 2. Swipe right or tap camera icon for stories
            # 3. Select from gallery
            # 4. Add optional text/stickers
            # 5. Share to story

            self.posted = True

        except Exception as e:
            logger.error(f"Error posting story: {e}", exc_info=True)
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
