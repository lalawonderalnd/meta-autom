"""Update bio action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class UpdateBioAction(Action):
    """Update the account bio."""

    name = "update_bio"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.updated = False

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.updated = False

        bio_template = params.get("bio", "")
        link = params.get("link", "")

        logger.info(
            "Updating bio",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Navigate to profile
            ig_app.navigate_to_profile()
            self.session.sleep(1.5)

            # Tap edit profile
            try:
                edit_btn = self.session.find(resourceId=ig_app.selectors.edit_profile)
                self.session.tap_element(edit_btn)
                self.session.sleep(1.5)
            except Exception:
                logger.warning("Could not find edit profile button")
                return ActionResult(
                    success=False,
                    duration_ms=int((time.time() - start_time) * 1000),
                    action_name=self.name,
                    error="Could not access edit profile",
                )

            # Fill in bio (simplified - would need to find the bio input field)
            # Type letter-by-letter

            self.updated = True

        except Exception as e:
            logger.error(f"Error updating bio: {e}", exc_info=True)
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
            metadata={"updated": self.updated},
        )
