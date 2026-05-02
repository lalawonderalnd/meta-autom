# AccFarm Orchestrator

The brain of AccFarm v2. Receives high-level intents from the dashboard, schedules them as discrete jobs, hands jobs to Celery workers, who in turn use the Device Layer (Layer 3) and Instagram Bot (Layer 4) to execute.

## Quick Start

```bash
# Install dependencies
uv sync

# Run local dev stack (Redis + API + Worker)
docker compose -f docker-compose.dev.yml up
```

## Architecture

- **FastAPI** HTTP API on port 8000
- **Celery** workers with per-device queues
- **Redis** as broker and result backend
- **PostgreSQL** (Supabase) for persistence
- **APScheduler** for periodic tasks via Celery beat

## Worker Setup

One worker per device queue:

```bash
# Spawn workers for all registered devices
python scripts/spawn_workers.py

# Or manually for a specific device
celery -A app.workers.celery_app worker -Q device.RZ8M601ABCD --concurrency=1 --loglevel=INFO
```

## API Endpoints

- `GET /healthz` - Health check
- `GET/POST /accounts` - List/create accounts
- `POST /accounts/{id}/jobs` - Queue a job
- `GET/POST /devices` - List/register devices
- `POST /devices/{id}/killswitch` - Emergency stop
- `GET/POST /jobs` - List/bulk dispatch jobs
- `WS /ws/sessions/{session_id}` - Live action stream

## State Machine

Accounts flow through states: NEW → WARMING → ACTIVE → (COOLDOWN|WARNING|BANNED|REMOVED)

See `app/state/machine.py` for the full transition matrix.

## Development

```bash
# Lint and format
ruff check . && ruff format .

# Run tests
pytest

# Seed demo data
python scripts/seed_demo_data.py
```
