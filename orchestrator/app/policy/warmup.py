"""Warmup curriculum - day-by-day plan generator."""

from dataclasses import dataclass, field


@dataclass
class SessionAction:
    """A single action in a session plan."""

    kind: str  # "browse", "like", "follow", "comment", "post", "story_view", "dm"
    count: int
    params: dict = field(default_factory=dict)


@dataclass
class SessionPlan:
    """A complete session plan for an account."""

    actions: list[SessionAction] = field(default_factory=list)
    duration_minutes: tuple[int, int] = (5, 10)  # (min, max)
    notes: str = ""


# Day-by-day warmup curriculum
WARMUP_CURRICULUM = {
    1: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (3, 7)}),
            SessionAction(kind="story_view", count=5, params={})),
        ],
        duration_minutes=(3, 7),
        notes="Browse only - open app, scroll feed, watch stories. No likes, no follows, no posts.",
    ),
    2: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (5, 10)}),
            SessionAction(kind="story_view", count=10, params={}),
            SessionAction(kind="like", count=5, params={"scatter": True}),
        ],
        duration_minutes=(5, 10),
        notes="Browse + 5 likes max. Scroll feed 5-10 min, watch 5-10 stories. Likes scattered across session.",
    ),
    3: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (8, 12)}),
            SessionAction(kind="story_view", count=15, params={}),
            SessionAction(kind="like", count=10, params={"scatter": True}),
            SessionAction(kind="follow", count=2, params={"via": "hashtag_exploration"}),
        ],
        duration_minutes=(8, 12),
        notes="Browse + 10 likes + 2 follows. Tap into 1-2 profiles via hashtag exploration.",
    ),
    4: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (10, 15)}),
            SessionAction(kind="story_view", count=20, params={}),
            SessionAction(kind="like", count=15, params={"scatter": True}),
            SessionAction(kind="follow", count=3, params={}),
            SessionAction(kind="profile_complete", count=1, params={"fields": ["bio", "avatar"]}),
        ],
        duration_minutes=(10, 15),
        notes="Browse + 15 likes + 3 follows + first profile completion (set bio, avatar). No posts yet.",
    ),
    5: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (10, 15)}),
            SessionAction(kind="story_view", count=25, params={}),
            SessionAction(kind="like", count=20, params={"scatter": True}),
            SessionAction(kind="follow", count=4, params={}),
            SessionAction(kind="post", count=1, params={"type": "feed", "stakes": "low"}),
        ],
        duration_minutes=(10, 15),
        notes="Browse + 20 likes + 4 follows + 1 light post (a low-stakes feed image, no link in caption).",
    ),
    6: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (12, 18)}),
            SessionAction(kind="story_view", count=30, params={}),
            SessionAction(kind="like", count=25, params={"scatter": True}),
            SessionAction(kind="follow", count=5, params={}),
            SessionAction(kind="post", count=1, params={"type": "reel"}),
        ],
        duration_minutes=(12, 18),
        notes="Browse + 25 likes + 5 follows + 1 reel + watch 15 stories.",
    ),
    7: SessionPlan(
        actions=[
            SessionAction(kind="browse", count=1, params={"duration_minutes": (15, 20)}),
            SessionAction(kind="story_view", count=35, params={}),
            SessionAction(kind="like", count=30, params={"scatter": True}),
            SessionAction(kind="follow", count=7, params={}),
            SessionAction(kind="post", count=1, params={"type": "reel"}),
            SessionAction(kind="comment", count=2, params={"engagement": "light"}),
            SessionAction(kind="dm", count=1, params={"type": "emoji", "target": "friendly"}),
        ],
        duration_minutes=(15, 20),
        notes="Browse + 30 likes + 7 follows + 1 reel + 2 comments + 1 DM (low-engagement, just emoji to a friendly account).",
    ),
}


class WarmupCurriculum:
    """Manages the warmup curriculum for accounts."""

    @staticmethod
    def get_day_plan(day: int) -> SessionPlan:
        """Get the session plan for a specific warmup day."""
        return WARMUP_CURRICULUM.get(day, SessionPlan(actions=[], notes=f"Unknown warmup day: {day}"))

    @staticmethod
    def get_total_days() -> int:
        """Get the total number of warmup days."""
        return len(WARMUP_CURRICULUM)


def build_warmup_plan(account: dict | None, day: int) -> SessionPlan:
    """
    Returns the SessionPlan the bot will execute today for this account.

    Args:
        account: Account dict (unused for now, but available for future customization)
        day: The current warmup day (1-7)

    Returns:
        SessionPlan for the given day
    """
    return WarmupCurriculum.get_day_plan(day)
