"""Account management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from accfarm_shared.db_models import Account, Device, Client, Session, Action
from accfarm_shared.enums import AccountStatus
from ..deps import CurrentUser, DbSession

router = APIRouter()


class AccountListResponse(BaseModel):
    """Response for listing accounts."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class AccountDetailResponse(BaseModel):
    """Response for account detail."""

    id: str
    username: str | None
    status: str
    device_id: str | None
    client_id: str | None
    created_at: str
    updated_at: str


class CreateJobRequest(BaseModel):
    """Request to create a job for an account."""

    kind: str
    payload: dict[str, Any] | None = None
    priority: int = 5
    scheduled_for: str | None = None


class TransitionRequest(BaseModel):
    """Request to manually transition account state."""

    new_status: str
    reason: str


@router.get("", response_model=AccountListResponse)
async def list_accounts(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    device_id: UUID | None = None,
    client_id: UUID | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> AccountListResponse:
    """List accounts with optional filters."""
    # Build query
    stmt = select(Account)
    
    # Apply filters
    if status_filter:
        try:
            status_enum = AccountStatus(status_filter.upper())
            stmt = stmt.where(Account.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
    if device_id:
        stmt = stmt.where(Account.device_id == device_id)
    
    if client_id:
        stmt = stmt.where(Account.client_id == client_id)
    
    if search:
        stmt = stmt.where(
            or_(
                Account.username.ilike(f"%{search}%"),
                Account.package_name.ilike(f"%{search}%"),
            )
        )
    
    # Get total count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    accounts = result.scalars().all()
    
    items = [
        {
            "id": str(acc.id),
            "username": acc.username,
            "status": acc.status.value,
            "device_id": str(acc.device_id) if acc.device_id else None,
            "client_id": str(acc.client_id) if acc.client_id else None,
            "warmup_day": acc.warmup_day,
            "health_score": acc.health_score,
            "created_at": acc.created_at.isoformat(),
        }
        for acc in accounts
    ]
    
    return AccountListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{account_id}", response_model=AccountDetailResponse)
async def get_account(db: DbSession, current_user: CurrentUser, account_id: UUID) -> AccountDetailResponse:
    """Get account by ID."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    return AccountDetailResponse(
        id=str(account.id),
        username=account.username,
        status=account.status.value,
        device_id=str(account.device_id) if account.device_id else None,
        client_id=str(account.client_id) if account.client_id else None,
        created_at=account.created_at.isoformat(),
        updated_at=account.updated_at.isoformat(),
    )


@router.patch("/{account_id}")
async def update_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update account notes, client_id, etc."""
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    
    # Allowed fields for update
    allowed_fields = {"client_id", "bio", "display_name", "profile_picture_url"}
    
    for field, value in updates.items():
        if field in allowed_fields and hasattr(account, field):
            setattr(account, field, value)
    
    await db.flush()
    
    return {"status": "updated", "id": str(account.id)}


@router.post("/{account_id}/jobs")
async def create_job_for_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    request: CreateJobRequest,
) -> dict[str, Any]:
    """Queue a job for this account."""
    from ..services.job_dispatcher import JobDispatcher

    dispatcher = JobDispatcher(db)
    try:
        job = await dispatcher.dispatch(
            kind=request.kind,
            account_id=account_id,
            payload=request.payload,
            priority=request.priority,
            scheduled_for=request.scheduled_for,
        )
        return {"id": job["id"], "status": "queued"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{account_id}/transition")
async def transition_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    request: TransitionRequest,
) -> dict[str, Any]:
    """Manual state transition (operator override)."""
    from ..state.machine import AccountStateMachine

    state_machine = AccountStateMachine(db, account_id)
    try:
        await state_machine.transition(
            new_status=request.new_status,
            reason=request.reason,
            actor=current_user.get("sub", "unknown"),
        )
        return {"status": "transitioned", "new_status": request.new_status}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("/{account_id}/sessions")
async def list_account_sessions(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get past sessions for an account."""
    from sqlalchemy import select
    
    stmt = select(Session).where(Session.account_id == account_id).order_by(Session.started_at.desc())
    
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    sessions = result.scalars().all()
    
    # Get total count
    count_stmt = select(func.count()).select_from(select(Session.id).where(Session.account_id == account_id).subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    items = [
        {
            "id": str(sess.id),
            "started_at": sess.started_at.isoformat(),
            "ended_at": sess.ended_at.isoformat() if sess.ended_at else None,
            "duration_seconds": sess.duration_seconds,
            "actions_summary": sess.actions_summary,
            "ended_reason": sess.ended_reason,
        }
        for sess in sessions
    ]
    
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{account_id}/actions")
async def list_account_actions(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get past actions for an account, paginated."""
    from sqlalchemy import select, join
    
    # Join actions with sessions to filter by account
    stmt = (
        select(Action)
        .join(Session, Action.session_id == Session.id)
        .where(Session.account_id == account_id)
        .order_by(Action.occurred_at.desc())
    )
    
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    actions = result.scalars().all()
    
    # Get total count
    count_stmt = select(func.count(Action.id)).join(Session, Action.session_id == Session.id).where(Session.account_id == account_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    items = [
        {
            "id": str(act.id),
            "kind": act.kind,
            "target": act.target,
            "success": act.success,
            "duration_ms": act.duration_ms,
            "occurred_at": act.occurred_at.isoformat(),
        }
        for act in actions
    ]
    
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.delete("/{account_id}")
async def remove_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
) -> dict[str, Any]:
    """Soft-remove an account (sets status=REMOVED)."""
    from ..state.machine import AccountStateMachine

    state_machine = AccountStateMachine(db, account_id)
    try:
        await state_machine.transition(
            new_status="REMOVED",
            reason="Operator removed account",
            actor=current_user.get("sub", "unknown"),
        )
        return {"status": "removed"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
