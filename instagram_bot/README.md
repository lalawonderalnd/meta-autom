# AccFarm Instagram Bot

Layer 4 behavior engine for AccFarm v2 — the part that actually opens Instagram, scrolls feed, taps like, types comments, and posts reels.

## Architecture

This bot runs on top of `accfarm_device.U2Session` (Layer 3) which wraps the physical phone via uiautomator2.

Key design principles:
- **Plugin-based action architecture** — each action is a self-contained module
- **Filters system** — profile and post filtering before interaction
- **Versioned selectors** — IG version → resource ID mapping
- **Humanized behavior** — variable timing, distractions, reading patterns
- **Checkpoint detection** — detect and escalate verification screens

## Installation

```bash
cd instagram_bot
uv sync
```

## Usage

```python
from accfarm_ig.runner import run_session
from accfarm_ig.plan import SessionPlan, ActionStep

plan = SessionPlan(
    account_id=account_uuid,
    intent="warmup",
    target_duration_seconds=300,
    steps=[
        ActionStep(action="browse_feed", max_duration_seconds=180),
        ActionStep(action="watch_stories", max_count=4),
    ],
    daily_caps_remaining={"likes": 0, "follows": 0, "comments": 0},
)

result = await run_session(session, account, plan)
```

## Structure

```
accfarm_ig/
├── runner.py           # Top-level session executor
├── plan.py             # SessionPlan + ActionStep models
├── ig_app.py           # Instagram app lifecycle
├── selectors/          # Versioned IG resource IDs
├── actions/            # Action implementations
├── warmup/             # Day 1-7 curriculum
├── filters/            # Profile/post filters
├── humanize_extras/    # Reading time, distractions, session shape
├── recovery/           # Checkpoint detection
├── content/            # Caption generation, hashtags
└── interacted_store.py # KV store for interacted usernames
```

## Development

```bash
# Run tests
pytest -m "not integration"

# Lint and type check
ruff check . && mypy accfarm_ig/
```
