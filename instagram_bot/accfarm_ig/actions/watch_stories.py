"""Watch stories action - view stories from the story tray."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

from accfarm_ig.actions.base import Action, ActionResult

if TYPE_CHECKING:
    from accfarm_device.u2_session import U2Session
    from accfarm_shared.models import Account

logger = logging.getLogger(__name__)


class WatchStoriesAction(Action):
    """Watch stories from the story tray with human-like behavior."""

    name = "watch_stories"

    def __init__(self, session: U2Session, account: Account):
        super().__init__(session, account)
        self.stories_watched = 0

    async def run(
        self, params: dict, max_count: int, max_duration: int | None
    ) -> ActionResult:
        """
        Watch stories from the story tray.

        Args:
            params: Optional params like {"pause_rate": 0.3} for tap-and-hold
            max_count: Maximum number of stories to watch
            max_duration: Maximum duration in seconds

        Returns:
            ActionResult with metadata about stories watched
        """
        start_time = time.time()
        self.stories_watched = 0

        pause_rate = params.get("pause_rate", 0.3)  # 30% chance to pause

        logger.info(
            f"Watching stories: max {max_count}",
            extra={"account_id": self.account.id},
        )

        try:
            from accfarm_ig.ig_app import InstagramApp
            ig_app = InstagramApp(self.session)
            ig_app.navigate_to_home()
            self.session.sleep(1.0)

            # Find the story tray
            story_tray = self.session.find(resourceId=ig_app.selectors.story_tray)
            if not story_tray.exists():
                logger.warning("Story tray not found")
                return ActionResult(
                    success=True,
                    duration_ms=int((time.time() - start_time) * 1000),
                    action_name=self.name,
                    metadata={"stories_watched": 0, "reason": "no_story_tray"},
                )

            # Tap on the first unseen story
            # In a real implementation, we'd find the first unwatched story circle
            # For now, tap the first story item we can find
            try:
                first_story = self.session.find(
                    resourceId="com.instagram.android:id/story_circle"
                )
                if first_story.exists():
                    self.session.tap_element(first_story)
                    self.session.sleep(1.5)  # Wait for story to open
                else:
                    logger.info("No stories available to watch")
                    return ActionResult(
                        success=True,
                        duration_ms=int((time.time() - start_time) * 1000),
                        action_name=self.name,
                        metadata={"stories_watched": 0, "reason": "no_stories"},
                    )
            except Exception:
                logger.info("Could not find story to open")
                return ActionResult(
                    success=True,
                    duration_ms=int((time.time() - start_time) * 1000),
                    action_name=self.name,
                    metadata={"stories_watched": 0, "reason": "could_not_open"},
                )

            # Watch stories (they auto-advance, but we simulate some interaction)
            while self.stories_watched < max_count:
                elapsed = time.time() - start_time
                if max_duration and elapsed >= max_duration:
                    break

                # Each story is typically 5-15 seconds
                # We'll watch for a portion of that
                watch_time = 3.0 + (time.time() % 4.0)  # 3-7 seconds per story

                # Occasionally pause (tap-and-hold) for realism
                if time.time() % 10 < pause_rate * 10:
                    # Simulate tap-and-hold by waiting longer
                    watch_time *= 1.5
                    logger.debug("Pausing on story (tap-and-hold)")

                self.session.sleep(watch_time)
                self.stories_watched += 1

                # Story auto-advances, but we can also tap to advance
                if time.time() % 7 < 2:
                    # Tap right side to advance (more intentional)
                    display_width = self.session._u2.info["displayWidth"]
                    self.session.tap(int(display_width * 0.75), int(display_width * 0.3))
                    self.session.sleep(0.5)

                # Check for warnings
                warning = self._check_for_warnings()
                if warning:
                    return ActionResult(
                        success=True,
                        duration_ms=int((time.time() - start_time) * 1000),
                        action_name=self.name,
                        metadata={"stories_watched": self.stories_watched},
                        warning=warning,
                    )

            # Go back to home feed
            self.session.press_back()
            self.session.sleep(0.8)

        except Exception as e:
            logger.error(f"Error watching stories: {e}", exc_info=True)
            return ActionResult(
                success=False,
                duration_ms=int((time.time() - start_time) * 1000),
                action_name=self.name,
                error=str(e),
                metadata={"stories_watched": self.stories_watched},
            )

        return ActionResult(
            success=True,
            duration_ms=int((time.time() - start_time) * 1000),
            action_name=self.name,
            metadata={"stories_watched": self.stories_watched},
        )
