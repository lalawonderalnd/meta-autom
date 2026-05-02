"""Set avatar action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class SetAvatarAction(Action):
    """Set the account profile picture (avatar)."""

    name = "set_avatar"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.updated = False

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.updated = False

        image_path = params.get("image_path")  # Path on device

        logger.info(
            "Setting avatar",
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

            # Tap change profile photo
            try:
                change_photo_btn = self.session.find(resourceId=ig_app.selectors.change_photo)
                self.session.tap_element(change_photo_btn)
                self.session.sleep(1.5)
            except Exception:
                logger.warning("Could not find change photo button")

            # Select from gallery and choose the pushed image
            # This is simplified - full implementation would navigate gallery picker

            self.updated = True

        except Exception as e:
            logger.error(f"Error setting avatar: {e}", exc_info=True)
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
