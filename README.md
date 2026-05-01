# AccFarm v2 — Master Architecture & Shared Contracts

> **READ THIS FIRST.** Every other prompt in this suite (`01_DASHBOARD.md`, `02_DEVICE_LAYER.md`, `03_ORCHESTRATOR.md`, `04_INSTAGRAM_BOT.md`, `05_SETUP.md`) assumes you have read and internalized this document. The shared database schema, API contracts, and folder structure live here — every component must conform to them.

---

## 1. What we are building

A self-hosted Instagram (and later TikTok) account farm that:

- Manages **5,000+ accounts** across a fleet of **physical Android phones** running **App Cloner** (10–20 clones per phone, real hardware = best detection survival).
- Each clone gets a **dedicated sticky residential mobile proxy** for life (IP rotation = ban).
- Provides a **cyberpunk-themed web dashboard** (matches the screenshot the operator already designed) with real-time account state, bulk operations, and live device mirroring via ws-scrcpy.
- Runs **multi-week warmup → posting → engagement** workflows with humanized behavior to evade Instagram's ML-based detection.
- Is built **modularly** so each layer (device, orchestrator, behavior, dashboard) can be replaced independently when platforms update their detection.

---

## 2. Open source projects we are standing on the shoulders of

The architecture distills lessons from the best free/open Instagram automation work that exists. We are NOT vendoring these — we are reimplementing the parts we need with our own contracts. But we honor what they got right.

| Project | What we steal |
|--------|---------------|
| **GramAddict** (`github.com/GramAddict/bot`) | YAML-driven action plugins, the filters system (`skip_if_private`, `min_followers`, `blacklist_words`, `biography_language`), letter-by-letter typing with autocomplete suggestions, session JSON format, Telegram reports |
| **uiautomator2** (`github.com/openatx/uiautomator2`) | The actual device control library. Lighter, faster, more reliable than Appium for our scale. Auto-installs ATX agent on device. |
| **Insomniac** (`github.com/alexal1/Insomniac`) | Recovery flows when Instagram throws checkpoints / "suspicious activity" screens |
| **appium-device-farm** (`github.com/AppiumTestDistribution/appium-device-farm`) | Hub/node device pool topology (we'll do a lighter Python version) |
| **ws-scrcpy** (`github.com/NetrisTV/ws-scrcpy`) | Browser-embedded live device view for the dashboard's "Watch" button |
| **App Cloner** (Yellow + Orange package) | Per-clone fingerprint randomization (Android ID, IMEI, IMSI, MAC, advertising IDs, build props), per-clone HTTP/SOCKS proxy override, Tasker integration for "regenerate identity" |

We are NOT using:
- Selenium / Appium for the bot itself (too heavy, too detectable, slower than uiautomator2)
- Emulators (Genymotion/BlueStacks/MEmu/LDPlayer — these are detected with >99% accuracy by modern fingerprint engines like Fingerprint.com, DeepID, etc.). **Real phones only for production.**
- iOS — Phase 2.

---

## 3. The four layers (and the four prompt documents)

```
┌────────────────────────────────────────────────────────────┐
│  LAYER 1: DASHBOARD          (01_DASHBOARD.md)             │
│  ─────────────────                                         │
│  • Next.js 15 + Supabase + Tailwind + shadcn/ui + TanStack │
│  • Reads account state, sends jobs, mirrors devices        │
│  • Cyberpunk dark theme (matches the Instagram-farm shot)  │
└────────────────────────────────────────────────────────────┘
                          ↕  Supabase Realtime + REST
┌────────────────────────────────────────────────────────────┐
│  LAYER 2: ORCHESTRATOR       (03_ORCHESTRATOR.md)          │
│  ─────────────────────                                     │
│  • FastAPI + Celery + Redis + Postgres (Supabase)          │
│  • Job scheduler, account state machine, behavior policy   │
│  • Routes jobs to least-loaded device worker               │
└────────────────────────────────────────────────────────────┘
                          ↕  internal Python imports + Redis
┌────────────────────────────────────────────────────────────┐
│  LAYER 3: DEVICE LAYER       (02_DEVICE_LAYER.md)          │
│  ──────────────────────                                    │
│  • Python service: device pool, ADB connection management  │
│  • Wraps uiautomator2 + adbutils + scrcpy                  │
│  • Exposes: connect, launch_clone, run_action, screenshot  │
└────────────────────────────────────────────────────────────┘
                          ↕  ADB-over-TCP/IP (port 5555)
┌────────────────────────────────────────────────────────────┐
│  LAYER 4: INSTAGRAM BOT      (04_INSTAGRAM_BOT.md)         │
│  ──────────────────────                                    │
│  • Action library: like, follow, scroll, post, comment, DM │
│  • Warmup state machine (DAY_1 .. DAY_7 .. ACTIVE)         │
│  • GramAddict-style filters + humanized behavior           │
│  • Captcha/checkpoint detection + recovery                 │
└────────────────────────────────────────────────────────────┘
                          ↕  uiautomator2 calls
┌────────────────────────────────────────────────────────────┐
│  PHYSICAL PHONES (set up via 05_SETUP.md)                  │
│  ────────────────                                          │
│  • Real Android 11+ devices                                │
│  • USB Debugging + Wi-Fi ADB enabled                       │
│  • App Cloner Premium + Yellow + Orange packages installed │
│  • Each clone has: random identity, sticky mobile proxy,   │
│    com.instagram.androidX package name                     │
└────────────────────────────────────────────────────────────┘
```

Each prompt document (01–04) is a self-contained Claude Code master prompt. Hand it to Claude Code, it builds that layer. They share the contracts defined below.

---

## 4. Folder structure (the monorepo)

```
accfarm/
├── README.md
├── docker-compose.yml          # Redis, Postgres (dev), wireguard-gateway (optional)
├── .env.example
│
├── dashboard/                  # Layer 1 — built by 01_DASHBOARD.md
│   ├── app/                    # Next.js 15 App Router
│   ├── components/
│   ├── lib/
│   ├── public/
│   └── package.json
│
├── orchestrator/               # Layer 2 — built by 03_ORCHESTRATOR.md
│   ├── app/
│   │   ├── api/                # FastAPI routes
│   │   ├── workers/            # Celery tasks
│   │   ├── state/              # Account state machine
│   │   ├── policy/             # Behavior policy engine
│   │   └── main.py
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
│
├── device_layer/               # Layer 3 — built by 02_DEVICE_LAYER.md
│   ├── accfarm_device/
│   │   ├── pool.py             # Device pool + connection management
│   │   ├── adb_client.py       # ADB wrapper
│   │   ├── u2_session.py       # uiautomator2 session wrapper
│   │   ├── clone.py            # App Cloner clone abstraction
│   │   ├── proxy.py            # Per-clone proxy management
│   │   ├── screen.py           # Screenshot/screencap
│   │   └── scrcpy_bridge.py    # Live view forwarding for dashboard
│   ├── tests/
│   └── pyproject.toml
│
├── instagram_bot/              # Layer 4 — built by 04_INSTAGRAM_BOT.md
│   ├── accfarm_ig/
│   │   ├── actions/
│   │   │   ├── base.py
│   │   │   ├── like.py
│   │   │   ├── follow.py
│   │   │   ├── scroll_feed.py
│   │   │   ├── watch_stories.py
│   │   │   ├── post.py
│   │   │   ├── comment.py
│   │   │   ├── direct_message.py
│   │   │   └── browse_profile.py
│   │   ├── warmup/             # Day-by-day warmup curriculum
│   │   ├── filters/            # GramAddict-style profile filters
│   │   ├── humanize/           # Bezier swipes, sleep distributions, typo injection
│   │   ├── recovery/           # Checkpoint detection + handlers
│   │   ├── selectors/          # Resource ID / xpath registry per IG version
│   │   └── runner.py           # Top-level: run_session(account, plan)
│   ├── tests/
│   └── pyproject.toml
│
├── shared/                     # Pydantic models + DB schema (read by all)
│   ├── accfarm_shared/
│   │   ├── models.py
│   │   ├── enums.py
│   │   └── db_schema.sql
│   └── pyproject.toml
│
└── infra/
    ├── supabase/
    │   └── migrations/
    └── scripts/
        ├── setup_phone.sh
        └── deploy.sh
```

**Why a monorepo:** the four layers share Pydantic models, DB schema, and enum definitions. Splitting into separate repos creates more pain than it solves at this stage.

---

## 5. Database schema (Postgres, hosted on Supabase)

This schema is **shared across all four layers**. The source of truth lives at `shared/accfarm_shared/db_schema.sql`. Every prompt below references it. Do not deviate.

```sql
-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE account_status AS ENUM (
  'NEW',              -- Just imported, no warmup yet
  'WARMING',          -- In warmup curriculum (days 1–7)
  'ACTIVE',           -- Healthy, posting/engaging
  'IDLE',             -- Manually paused
  'COOLDOWN',         -- Auto-paused after suspicious signal
  'NEEDS_ATTENTION',  -- Captcha / verification needed
  'WARNING',          -- IG threw a soft warning
  'SHADOWBANNED',     -- Detected reduced reach
  'BANNED',           -- Hard ban, dead
  'REMOVED'           -- Operator marked for removal
);

CREATE TYPE platform AS ENUM ('instagram', 'tiktok');

CREATE TYPE device_status AS ENUM (
  'ONLINE', 'OFFLINE', 'BUSY', 'ERROR'
);

CREATE TYPE job_status AS ENUM (
  'QUEUED', 'RUNNING', 'SUCCESS', 'FAILED', 'CANCELLED'
);

CREATE TYPE job_kind AS ENUM (
  'WARMUP_SESSION',
  'POST_CONTENT',
  'ENGAGE_HASHTAG',
  'ENGAGE_FOLLOWERS',
  'WATCH_STORIES',
  'CHECK_HEALTH',
  'RECOVER_CHECKPOINT'
);

-- ============================================================
-- TABLES
-- ============================================================

-- A real Android phone
CREATE TABLE devices (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  serial TEXT UNIQUE NOT NULL,         -- ADB serial
  name TEXT NOT NULL,                  -- Operator-friendly name (e.g. "Pixel-7-Rack-A-3")
  ip_address INET,                     -- For Wi-Fi ADB
  adb_port INT DEFAULT 5555,
  android_version TEXT,
  manufacturer TEXT,
  model TEXT,
  status device_status NOT NULL DEFAULT 'OFFLINE',
  max_clones INT NOT NULL DEFAULT 15,  -- Soft cap per phone
  current_clone_count INT NOT NULL DEFAULT 0,
  last_heartbeat TIMESTAMPTZ,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- A creator (the talent we're driving traffic to)
CREATE TABLE clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,                  -- e.g. "Lola"
  slug TEXT UNIQUE NOT NULL,           -- e.g. "lola"
  link_in_bio TEXT,                    -- bink.bio URL pushed to all accounts
  niche TEXT,                          -- e.g. "fitness", "cosplay", "alt"
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- A cloned Instagram app on a specific phone, hosting a single account
CREATE TABLE accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  platform platform NOT NULL DEFAULT 'instagram',
  username TEXT NOT NULL,
  password_encrypted TEXT NOT NULL,    -- AES-GCM, key in Vault
  email TEXT,
  email_password_encrypted TEXT,
  phone_number TEXT,                   -- The SMS number used at signup
  package_name TEXT NOT NULL,          -- e.g. com.instagram.androidp7
  device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
  client_id UUID REFERENCES clients(id) ON DELETE SET NULL,
  status account_status NOT NULL DEFAULT 'NEW',
  warmup_day INT NOT NULL DEFAULT 0,   -- 0 = NEW, 1–7 = warmup curriculum
  posts_count INT NOT NULL DEFAULT 0,
  followers_count INT NOT NULL DEFAULT 0,
  following_count INT NOT NULL DEFAULT 0,
  proxy_id UUID,                       -- FK below (declared after proxies table)
  identity JSONB NOT NULL DEFAULT '{}',-- App Cloner identity values
  bio TEXT,
  display_name TEXT,
  profile_picture_url TEXT,
  last_session_at TIMESTAMPTZ,
  last_health_check_at TIMESTAMPTZ,
  health_score NUMERIC(3,2) DEFAULT 1.00,  -- 0.00–1.00
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(platform, username)
);

CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_device ON accounts(device_id);
CREATE INDEX idx_accounts_client ON accounts(client_id);

-- One sticky residential mobile proxy per clone
CREATE TABLE proxies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,              -- 'iproyal', 'smartproxy', 'soax', etc.
  protocol TEXT NOT NULL,              -- 'http' | 'socks5'
  host TEXT NOT NULL,
  port INT NOT NULL,
  username TEXT,
  password_encrypted TEXT,
  country_code TEXT,                   -- ISO-3166 alpha-2
  city TEXT,
  carrier TEXT,
  sticky_session_id TEXT,              -- For providers that support it
  last_ip TEXT,
  last_ip_check_at TIMESTAMPTZ,
  is_alive BOOLEAN NOT NULL DEFAULT TRUE,
  bandwidth_used_mb NUMERIC DEFAULT 0,
  account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE accounts
  ADD CONSTRAINT fk_account_proxy FOREIGN KEY (proxy_id)
  REFERENCES proxies(id) ON DELETE SET NULL;

-- Discrete units of work the orchestrator hands out
CREATE TABLE jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kind job_kind NOT NULL,
  account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
  device_id UUID REFERENCES devices(id),
  status job_status NOT NULL DEFAULT 'QUEUED',
  priority INT NOT NULL DEFAULT 5,     -- 1=urgent, 9=background
  payload JSONB NOT NULL DEFAULT '{}', -- kind-specific config
  result JSONB,                        -- success metrics or error info
  scheduled_for TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  attempt INT NOT NULL DEFAULT 0,
  max_attempts INT NOT NULL DEFAULT 3,
  error_message TEXT,
  celery_task_id TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status_scheduled ON jobs(status, scheduled_for);
CREATE INDEX idx_jobs_account ON jobs(account_id);
CREATE INDEX idx_jobs_device ON jobs(device_id);

-- A single bot session (one app launch → close cycle)
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  duration_seconds INT,
  ig_app_version TEXT,
  actions_summary JSONB NOT NULL DEFAULT '{}',  -- {likes:5, follows:3, ...}
  ended_reason TEXT,                            -- 'completed', 'checkpoint', 'crash', 'killswitch'
  ended_with_warning BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_sessions_account ON sessions(account_id);

-- Individual atomic actions taken in a session
CREATE TABLE actions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,                  -- 'like', 'follow', 'scroll', 'view_story', 'post'
  target TEXT,                         -- username/hashtag/post_id
  success BOOLEAN NOT NULL,
  duration_ms INT,
  metadata JSONB,
  occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_actions_session ON actions(session_id);
CREATE INDEX idx_actions_kind_time ON actions(kind, occurred_at);

-- Content queue (videos/images ready to post)
CREATE TABLE content_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  storage_url TEXT NOT NULL,           -- Cloudflare R2 / S3 URL
  storage_path TEXT NOT NULL,
  caption TEXT,                        -- Master caption — bot rewrites per post
  hashtag_pool JSONB NOT NULL DEFAULT '[]',
  content_type TEXT NOT NULL,          -- 'reel', 'feed_post', 'story'
  duration_seconds INT,
  posted_count INT NOT NULL DEFAULT 0,
  max_posts INT NOT NULL DEFAULT 30,   -- Don't spam same content forever
  hash_signature TEXT,                 -- For dedup detection
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Logbook of every post a clone made
CREATE TABLE posts_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  content_item_id UUID REFERENCES content_items(id),
  ig_media_id TEXT,                    -- If we can scrape it back
  caption_used TEXT,
  hashtags_used JSONB,
  posted_at TIMESTAMPTZ DEFAULT NOW(),
  views INT,
  likes INT,
  comments INT,
  last_stats_at TIMESTAMPTZ
);

-- Operator audit log
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  actor TEXT,                          -- email or 'system'
  action TEXT NOT NULL,
  entity_type TEXT,
  entity_id TEXT,
  diff JSONB,
  occurred_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 6. Shared Pydantic models (`shared/accfarm_shared/models.py`)

Every layer that speaks Python imports from here. These mirror the DB schema.

```python
from datetime import datetime
from enum import Enum
from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, Field

class AccountStatus(str, Enum):
    NEW = "NEW"
    WARMING = "WARMING"
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    COOLDOWN = "COOLDOWN"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    WARNING = "WARNING"
    SHADOWBANNED = "SHADOWBANNED"
    BANNED = "BANNED"
    REMOVED = "REMOVED"

class JobKind(str, Enum):
    WARMUP_SESSION = "WARMUP_SESSION"
    POST_CONTENT = "POST_CONTENT"
    ENGAGE_HASHTAG = "ENGAGE_HASHTAG"
    ENGAGE_FOLLOWERS = "ENGAGE_FOLLOWERS"
    WATCH_STORIES = "WATCH_STORIES"
    CHECK_HEALTH = "CHECK_HEALTH"
    RECOVER_CHECKPOINT = "RECOVER_CHECKPOINT"

class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Account(BaseModel):
    id: UUID
    username: str
    package_name: str
    device_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    status: AccountStatus
    warmup_day: int = 0
    proxy_id: Optional[UUID] = None
    health_score: float = 1.0
    last_session_at: Optional[datetime] = None

class Device(BaseModel):
    id: UUID
    serial: str
    name: str
    ip_address: Optional[str]
    adb_port: int = 5555
    status: str
    max_clones: int = 15
    current_clone_count: int = 0

class Job(BaseModel):
    id: UUID
    kind: JobKind
    account_id: Optional[UUID]
    device_id: Optional[UUID]
    status: JobStatus
    priority: int = 5
    payload: dict[str, Any] = Field(default_factory=dict)
    scheduled_for: datetime
    attempt: int = 0
    max_attempts: int = 3

class ActionResult(BaseModel):
    """Returned by every bot action."""
    success: bool
    duration_ms: int
    target: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    warning: Optional[str] = None  # 'rate_limit', 'captcha_seen', 'block', etc.

class SessionResult(BaseModel):
    """Returned by runner.run_session()."""
    session_id: UUID
    success: bool
    duration_seconds: int
    actions_summary: dict[str, int]
    ended_reason: str
    health_delta: float = 0.0  # Adjustment to account health_score
    new_status: Optional[AccountStatus] = None  # If session forced a state change
```

---

## 7. Inter-layer API contracts

### Dashboard ↔ Orchestrator
HTTP REST + Supabase Realtime (Postgres listen/notify under the hood).

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/accounts` | List, filter, paginate |
| GET | `/accounts/{id}` | Detail |
| POST | `/accounts/{id}/jobs` | Queue a job for an account |
| POST | `/accounts/bulk` | Bulk action (warmup all NEW, pause all WARNING, etc.) |
| GET | `/devices` | Device pool state |
| GET | `/jobs?status=...` | Jobs view |
| POST | `/devices/{id}/scan` | Scan for new App Cloner clones |
| GET | `/devices/{id}/stream` | WebSocket → ws-scrcpy bridge |

Realtime: dashboard subscribes to `accounts`, `jobs`, `devices` tables — Supabase pushes diffs. The "ACTIVE" pill in the screenshot updates on Postgres NOTIFY.

### Orchestrator ↔ Device Layer
Internal Python imports (same Celery worker process). The orchestrator does:

```python
from accfarm_device.pool import DevicePool
from accfarm_device.u2_session import U2Session

with DevicePool().acquire(device_id, account_id, timeout=60) as session:
    # session is a U2Session bound to one clone on one phone
    runner.run_session(session, account, plan)
```

### Device Layer ↔ Phone
ADB over TCP/IP (port 5555), uiautomator2 over its ATX-agent on the device (port 7912 forwarded via ADB).

### Bot ↔ Device
The Bot layer NEVER opens raw ADB. It only takes a `U2Session` from the Device Layer and calls high-level methods on it. This is the abstraction boundary that keeps detection-evasion logic in one place.

---

## 8. Environment variables (`.env.example`)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/accfarm
SUPABASE_URL=https://xxx.supabase.co 
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_KEY=eyJ...

# Redis (Celery broker + cache)
REDIS_URL=redis://localhost:6379/0

# Encryption
ACCFARM_AES_KEY=                       # 32 bytes base64 — for password fields
JWT_SECRET=

# ADB
ADB_HOST=                              # leave empty for local; set for remote ADB hub
ADB_PORT=5037

# Proxies
PROXY_PROVIDER=iproyal
IPROYAL_USERNAME=
IPROYAL_PASSWORD=

# Notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_OPS_CHAT_ID=

# Storage
R2_ACCOUNT_ID=
R2_ACCESS_KEY=
R2_SECRET_KEY=
R2_BUCKET=accfarm-content
```

---

## 9. The ten unbreakable rules (every layer enforces these)

1. **One IP per clone for life.** Never rotate a proxy mid-account-life. If the proxy dies, mark the account COOLDOWN and notify ops.
2. **Real phones only.** Emulators are detected. App Cloner explicitly does not work on rooted/emulated devices anyway.
3. **Max 15 clones per phone (default).** Push higher only after thermal/perf benchmarks per phone model.
4. **Warmup is sacred.** Day 1 = browse only, no actions. Day 7 = act like a casual user. Skipping warmup = ~80% ban rate in the first week.
5. **Humanize every input.** Bezier-curve swipes, log-normal sleep distributions, occasional typos that get corrected, fake-tab-suggestions when typing. Naive `adb input tap 540 1200` is DEAD.
6. **Daily action caps per account.** Hard ceilings: 30 likes, 15 follows, 5 comments, 2 DMs, 1 post per 24h during warmup. Loosen gradually for ACTIVE accounts.
7. **One operation at a time per phone.** Two clones never both control the foreground. The DevicePool enforces a per-phone mutex.
8. **Checkpoint is a hard stop.** If IG asks for verification → status NEEDS_ATTENTION → notify ops → no further auto-attempts.
9. **All actions logged.** Every tap, swipe, and outcome lands in the `actions` table. This is your audit trail and your training data.
10. **Killswitch on each phone.** A red button in the dashboard immediately stops all jobs on that phone, force-closes IG clones, disconnects ADB. Operator panic button.

---

## 10. Setup order (what happens this weekend)

Follow `05_SETUP.md` for the physical phone setup. Then build in this order:

**Saturday morning (3h)** — Foundation
1. Spin up Supabase project + run `db_schema.sql`
2. Build `shared/` package (Pydantic models, encryption helpers)
3. Build `device_layer/` skeleton (`02_DEVICE_LAYER.md`) — get one phone connected, one clone launched, one screenshot taken

**Saturday afternoon (3h)** — Orchestrator skeleton
4. Build `orchestrator/` skeleton (`03_ORCHESTRATOR.md`) — Celery + Redis, one job kind (CHECK_HEALTH), end-to-end queue → execute → record

**Saturday evening (2h)** — Dashboard skeleton
5. Build `dashboard/` skeleton (`01_DASHBOARD.md`) — accounts table reading from Supabase, looks like the screenshot

**Sunday morning (3h)** — Real bot actions
6. Build `instagram_bot/` first action: `scroll_feed` (`04_INSTAGRAM_BOT.md`)
7. Wire it: dashboard → queue WARMUP_SESSION → orchestrator → device → bot → records back

**Sunday afternoon (3h)** — Warmup curriculum
8. Implement warmup days 1–3 (browse-only, light likes)
9. Test on 3 pilot accounts on one phone

**Sunday evening (2h)** — Posting
10. Implement `post_reel` action with content from R2
11. End-to-end: queue POST_CONTENT → see post live on Instagram

After this weekend you have a working farm controlling 3 accounts on one phone. Scaling to 5,000 is then a function of: more phones, more proxies, content pipeline, warmup-progression cron jobs, monitoring.

---

## 11. What's explicitly out of scope for the first build

- Account creation engine (5sim/SMS-Activate signup automation) → Phase 2
- TikTok adapter → Phase 3
- ML-based shadowban detection → Phase 3 (heuristic-only for now)
- Comment/DM AI personalization (Claude Sonnet integration) → Phase 2
- iOS support → not planned

These are noted in 04_INSTAGRAM_BOT.md as extension points. Do not let scope creep block the V1.

---

**Ready to build. Read the next four documents in order: `01_DASHBOARD.md`, `02_DEVICE_LAYER.md`, `03_ORCHESTRATOR.md`, `04_INSTAGRAM_BOT.md`. Hand each one to Claude Code as a separate session.**
