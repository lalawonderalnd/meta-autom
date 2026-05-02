"""Daily action caps per account+platform."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionLimits:
    """Hard ceilings per account per 24h."""

    likes_per_day: int = 0
    follows_per_day: int = 0
    unfollows_per_day: int = 0
    comments_per_day: int = 0
    dms_per_day: int = 0
    posts_per_day: int = 0
    story_views_per_day: int = 0
    sessions_per_day: int = 0
    min_minutes_between_sessions: int = 0

    @classmethod
    def zero(cls) -> "ActionLimits":
        """Return limits that allow no actions."""
        return cls()

    @classmethod
    def passive_only(cls) -> "ActionLimits":
        """Return limits that only allow passive actions (browse, view stories)."""
        return cls(
            story_views_per_day=50,
            sessions_per_day=2,
            min_minutes_between_sessions=120,
        )

    @classmethod
    def warming_day(cls, day: int) -> "ActionLimits":
        """Return limits for a specific warmup day."""
        # Day-by-day progressive limits
        limits = {
            1: cls(story_views_per_day=10, sessions_per_day=1, min_minutes_between_sessions=1440),
            2: cls(likes_per_day=5, story_views_per_day=20, sessions_per_day=1, min_minutes_between_sessions=1440),
            3: cls(
                likes_per_day=10,
                follows_per_day=2,
                story_views_per_day=30,
                sessions_per_day=2,
                min_minutes_between_sessions=180,
            ),
            4: cls(
                likes_per_day=15,
                follows_per_day=3,
                story_views_per_day=40,
                sessions_per_day=2,
                min_minutes_between_sessions=180,
            ),
            5: cls(
                likes_per_day=20,
                follows_per_day=4,
                posts_per_day=1,
                story_views_per_day=50,
                sessions_per_day=2,
                min_minutes_between_sessions=180,
            ),
            6: cls(
                likes_per_day=25,
                follows_per_day=5,
                posts_per_day=1,
                story_views_per_day=60,
                sessions_per_day=3,
                min_minutes_between_sessions=120,
            ),
            7: cls(
                likes_per_day=30,
                follows_per_day=7,
                comments_per_day=2,
                dms_per_day=1,
                posts_per_day=1,
                story_views_per_day=70,
                sessions_per_day=3,
                min_minutes_between_sessions=120,
            ),
        }
        return limits.get(day, cls.zero())


# Limits by account status
LIMITS_BY_STATUS = {
    "WARMING": lambda day: ActionLimits.warming_day(day),
    "ACTIVE": ActionLimits(
        likes_per_day=80,
        follows_per_day=20,
        unfollows_per_day=20,
        comments_per_day=8,
        dms_per_day=3,
        posts_per_day=2,
        story_views_per_day=200,
        sessions_per_day=4,
        min_minutes_between_sessions=90,
    ),
    "COOLDOWN": ActionLimits.zero(),
    "WARNING": ActionLimits.passive_only(),
    "NEEDS_ATTENTION": ActionLimits.zero(),
    "SHADOWBANNED": ActionLimits.zero(),
    "BANNED": ActionLimits.zero(),
    "IDLE": ActionLimits.zero(),
    "REMOVED": ActionLimits.zero(),
    "NEW": ActionLimits.zero(),
}


def get_limits_for_status(status: str, warmup_day: int | None = None) -> ActionLimits:
    """Get the action limits for a given account status."""
    limits = LIMITS_BY_STATUS.get(status, ActionLimits.zero())
    if callable(limits) and warmup_day is not None:
        return limits(warmup_day)
    elif callable(limits):
        return ActionLimits.zero()
    return limits
