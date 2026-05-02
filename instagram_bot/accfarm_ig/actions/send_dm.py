"""Send DM action."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class SendDmAction(Action):
    """Send direct messages."""

    name = "send_dm"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.messages_sent = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        start_time = time.time()
        self.messages_sent = 0

        recipient = params.get("recipient")
        message = params.get("message", "Hello!")

        logger.info(
            f"Sending DM to: {recipient}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)

            # Navigate to messages
            # Tap on the messages icon in top right of home
            
            while self.messages_sent < max_count:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                # Find and tap message input
                try:
                    msg_input = self.session.find(resourceId=ig_app.selectors.message_input)
                    self.session.tap_element(msg_input)
                    self.session.sleep(0.5)
                    
                    # Type message
                    self.session.type_text(message)
                    self.session.sleep(1.0)
                    
                    # Tap send
                    send_btn = self.session.find(resourceId=ig_app.selectors.message_send)
                    self.session.tap_element(send_btn)
                    self.messages_sent += 1
                    
                    self.session.sleep(2.0)
                except Exception as e:
                    logger.warning(f"Could not send DM: {e}")
                    break

        except Exception as e:
            logger.error(f"Error sending DM: {e}", exc_info=True)
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
            metadata={"messages_sent": self.messages_sent},
        )
