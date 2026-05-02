"""
Debug Replay API - Session replay, dry-run mode, and one-click reset.

Provides developer experience tools for debugging account issues,
simulating actions, and resetting account state.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from supabase import Client


router = APIRouter(prefix="/api/debug", tags=["debug"])


# Request/Response models

class SessionReplayRequest(BaseModel):
    account_id: str
    start_time: str
    end_time: str
    action_types: Optional[List[str]] = None


class SessionReplayResponse(BaseModel):
    account_id: str
    session_start: str
    session_end: str
    actions: List[dict]
    summary: dict


class DryRunRequest(BaseModel):
    account_id: str
    action_type: str
    parameters: Optional[dict] = None
    simulate_delay: bool = True


class DryRunResponse(BaseModel):
    success: bool
    simulated_action: dict
    predicted_outcome: str
    warnings: List[str]
    would_execute: bool


class AccountResetRequest(BaseModel):
    account_id: str
    reset_type: str  # full, warmup_only, session_only, identity_only
    confirm: bool


class AccountResetResponse(BaseModel):
    success: bool
    account_id: str
    reset_type: str
    changes_applied: List[str]
    timestamp: str


# Helper to get Supabase client
def get_supabase() -> Client:
    # In real implementation, this would come from app state
    raise HTTPException(status_code=500, detail="Supabase client not configured")


@router.get("/sessions/{account_id}", response_model=SessionReplayResponse)
async def get_session_replay(
    account_id: str,
    start_time: str,
    end_time: str,
    action_types: Optional[str] = None
):
    """
    Replay all actions for an account within a time window.
    
    Useful for debugging what led to a ban or warning state.
    Shows exact sequence of actions with timestamps.
    """
    supabase = get_supabase()
    
    # Parse time range
    try:
        start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {e}")
    
    # Build query
    query = supabase.table("actions").select("""
        *,
        accounts(username, status)
    """).eq("actor_account_id", account_id).gte("created_at", start_time).lte("created_at", end_time).order("created_at")
    
    if action_types:
        types = action_types.split(",")
        query = query.in_("kind", types)
    
    result = query.execute()
    actions = result.data or []
    
    if not actions:
        raise HTTPException(status_code=404, detail="No actions found in time range")
    
    # Generate summary
    action_counts = {}
    for action in actions:
        kind = action.get("kind", "unknown")
        action_counts[kind] = action_counts.get(kind, 0) + 1
    
    return SessionReplayResponse(
        account_id=account_id,
        session_start=start_time,
        session_end=end_time,
        actions=actions,
        summary={
            "total_actions": len(actions),
            "action_breakdown": action_counts,
            "duration_minutes": (end - start).total_seconds() / 60,
            "actions_per_minute": len(actions) / max(1, (end - start).total_seconds() / 60),
        }
    )


@router.post("/dry-run", response_model=DryRunResponse)
async def dry_run_action(request: DryRunRequest):
    """
    Simulate an action without executing it.
    
    Shows what would happen if the action were executed,
    including any validation failures or rate limit issues.
    """
    supabase = get_supabase()
    
    warnings = []
    predicted_outcome = "success"
    
    # Fetch account to check state
    account_result = supabase.table("accounts").select("""
        *,
        devices(adb_status),
        proxies(is_alive, country)
    """).eq("id", request.account_id).execute()
    
    if not account_result.data:
        raise HTTPException(status_code=404, detail="Account not found")
    
    account = account_result.data[0]
    
    # Check account status
    if account.get("status") == "BANNED":
        predicted_outcome = "failed - account is banned"
        warnings.append("Account is banned - action will not succeed")
    elif account.get("status") == "REMOVED":
        predicted_outcome = "failed - account is removed"
        warnings.append("Account is removed - action will not succeed")
    elif account.get("status") == "COOLDOWN":
        cooldown_until = account.get("cooldown_until")
        if cooldown_until:
            try:
                cooldown_time = datetime.fromisoformat(cooldown_until)
                if datetime.utcnow() < cooldown_time:
                    predicted_outcome = "failed - account is in cooldown"
                    warnings.append(f"Account in cooldown until {cooldown_until}")
            except ValueError:
                pass
    
    # Check device status
    device = account.get("devices")
    if device and device.get("adb_status") != "online":
        warnings.append(f"Device is {device.get('adb_status')} - may not be able to execute")
    
    # Check proxy status
    proxy = account.get("proxies")
    if proxy and not proxy.get("is_alive"):
        warnings.append("Proxy is marked as dead - consider switching")
    
    # Check rate limits based on recent actions
    recent_actions = supabase.table("actions").select("created_at").eq(
        "actor_account_id", request.account_id
    ).gte("created_at", (datetime.utcnow().replace(hour=0, minute=0, second=0)).isoformat()).execute()
    
    today_count = len(recent_actions.data or [])
    if today_count > 50:
        warnings.append(f"High activity today ({today_count} actions) - approaching rate limits")
    if today_count > 80:
        predicted_outcome = "risky - very high activity today"
        warnings.append("CRITICAL: Very close to daily limits")
    
    # Simulate the action
    simulated_action = {
        "account_id": request.account_id,
        "action_type": request.action_type,
        "parameters": request.parameters,
        "account_status": account.get("status"),
        "device_status": device.get("adb_status") if device else "unknown",
        "proxy_country": proxy.get("country") if proxy else "unknown",
        "today_action_count": today_count,
    }
    
    would_execute = len(warnings) == 0 or (predicted_outcome == "success" and len(warnings) <= 1)
    
    return DryRunResponse(
        success=predicted_outcome == "success",
        simulated_action=simulated_action,
        predicted_outcome=predicted_outcome,
        warnings=warnings,
        would_execute=would_execute
    )


@router.post("/accounts/{account_id}/reset", response_model=AccountResetResponse)
async def reset_account(request: AccountResetRequest):
    """
    Reset account state for troubleshooting.
    
    Types:
    - full: Complete reset (warmup, sessions, identity flags)
    - warmup_only: Reset warmup progress to day 0
    - session_only: Clear active session and job
    - identity_only: Regenerate identity markers
    """
    if not request.confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must set confirm=true to reset account. This action cannot be undone."
        )
    
    supabase = get_supabase()
    changes_applied = []
    now = datetime.utcnow().isoformat()
    
    # Fetch current account state
    account_result = supabase.table("accounts").select("*").eq("id", request.account_id).execute()
    
    if not account_result.data:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = {}
    
    if request.reset_type == "full" or request.reset_type == "warmup_only":
        update_data["warmup_day"] = 0
        update_data["warmup_started_at"] = None
        update_data["warmup_completed_at"] = None
        changes_applied.append("Reset warmup progress to day 0")
    
    if request.reset_type == "full" or request.reset_type == "session_only":
        # Cancel any running jobs
        supabase.table("jobs").update({
            "status": "CANCELLED",
            "error_message": "Cancelled by account reset",
        }).eq("account_id", request.account_id).eq("status", "RUNNING").execute()
        
        update_data["current_job_id"] = None
        update_data["last_action_at"] = None
        changes_applied.append("Cleared active session and cancelled running jobs")
    
    if request.reset_type == "full" or request.reset_type == "identity_only":
        update_data["requires_identity_refresh"] = True
        changes_applied.append("Marked for identity refresh on next run")
    
    if request.reset_type == "full":
        update_data["status"] = "WARMING"
        update_data["warning_reason"] = None
        update_data["error_count"] = 0
        changes_applied.append("Reset status to WARMING and cleared errors")
    
    # Apply updates
    if update_data:
        update_data["updated_at"] = now
        supabase.table("accounts").update(update_data).eq("id", request.account_id).execute()
    
    # Log the reset action
    supabase.table("audit_log").insert({
        "action": "account_reset",
        "target_type": "account",
        "target_id": request.account_id,
        "details": {
            "reset_type": request.reset_type,
            "changes": changes_applied,
        },
        "created_at": now,
    }).execute()
    
    return AccountResetResponse(
        success=True,
        account_id=request.account_id,
        reset_type=request.reset_type,
        changes_applied=changes_applied,
        timestamp=now
    )


@router.get("/accounts/{account_id}/timeline")
async def get_account_timeline(account_id: str, hours: int = 24):
    """
    Get a timeline of all events for an account.
    
    Combines actions, jobs, and status changes into a single timeline.
    """
    supabase = get_supabase()
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    
    timeline = []
    
    # Fetch actions
    actions = supabase.table("actions").select("kind, created_at, details").eq(
        "actor_account_id", account_id
    ).gte("created_at", since).order("created_at").execute()
    
    for action in (actions.data or []):
        timeline.append({
            "type": "action",
            "timestamp": action.get("created_at"),
            "event": action.get("kind"),
            "details": action.get("details"),
        })
    
    # Fetch jobs
    jobs = supabase.table("jobs").select("kind, status, created_at, completed_at, error_message").eq(
        "account_id", account_id
    ).gte("created_at", since).order("created_at").execute()
    
    for job in (jobs.data or []):
        timeline.append({
            "type": "job",
            "timestamp": job.get("created_at"),
            "event": f"Job {job.get('kind')} {job.get('status')}",
            "details": {
                "status": job.get("status"),
                "error": job.get("error_message"),
                "completed": job.get("completed_at"),
            },
        })
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x.get("timestamp", ""))
    
    return {
        "account_id": account_id,
        "period_hours": hours,
        "events": timeline,
        "total_events": len(timeline),
    }


@router.post("/simulate/ban-wave")
async def simulate_ban_wave(percentage: float = 5.0):
    """
    SIMULATION ONLY: Test how the system responds to a ban wave.
    
    Marks a percentage of accounts as banned to test alerting and
    auto-recovery systems. Only works in simulation mode.
    """
    # Check if simulation mode is enabled
    import os
    if os.getenv("SIMULATION_MODE", "false").lower() != "true":
        raise HTTPException(
            status_code=403, 
            detail="Simulation mode not enabled. Set SIMULATION_MODE=true to use."
        )
    
    supabase = get_supabase()
    
    # Get random sample of accounts
    accounts = supabase.table("accounts").select("id, username").eq("status", "ACTIVE").execute()
    
    if not accounts.data:
        return {"message": "No active accounts to simulate"}
    
    import random
    num_to_ban = max(1, int(len(accounts.data) * percentage / 100))
    to_ban = random.sample(accounts.data, num_to_ban)
    
    banned_ids = [a["id"] for a in to_ban]
    
    # Mark as banned
    supabase.table("accounts").update({
        "status": "BANNED",
        "warning_reason": "SIMULATION: Ban wave test",
        "banned_at": datetime.utcnow().isoformat(),
    }).in_("id", banned_ids).execute()
    
    return {
        "simulation": True,
        "accounts_affected": len(banned_ids),
        "percentage": percentage,
        "banned_accounts": [{"id": a["id"], "username": a["username"]} for a in to_ban],
    }


@router.get("/health/check")
async def health_check():
    """
    Quick health check endpoint for monitoring.
    """
    supabase = get_supabase()
    
    try:
        # Test DB connection
        result = supabase.table("devices").select("id").limit(1).execute()
        db_ok = True
    except Exception as e:
        db_ok = False
    
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "timestamp": datetime.utcnow().isoformat(),
    }
