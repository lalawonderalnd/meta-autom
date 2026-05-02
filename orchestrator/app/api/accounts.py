"""Account management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    # TODO: Implement full query with filters
    # For now, return empty placeholder
    return AccountListResponse(items=[], total=0, page=page, page_size=page_size)


@router.get("/{account_id}", response_model=AccountDetailResponse)
async def get_account(db: DbSession, current_user: CurrentUser, account_id: UUID) -> AccountDetailResponse:
    """Get account by ID."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.patch("/{account_id}")
async def update_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update account notes, client_id, etc."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")


@router.post("/{account_id}/jobs")
async def create_job_for_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    request: CreateJobRequest,
) -> dict[str, Any]:
    """Queue a job for this account."""
    # TODO: Implement via JobDispatcher
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
        return {"id": str(job.id), "status": "queued"}
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
    # TODO: Implement via AccountStateMachine
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
    # TODO: Implement
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.get("/{account_id}/actions")
async def list_account_actions(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Get past actions for an account, paginated."""
    # TODO: Implement
    return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.delete("/{account_id}")
async def remove_account(
    db: DbSession,
    current_user: CurrentUser,
    account_id: UUID,
) -> dict[str, Any]:
    """Soft-remove an account (sets status=REMOVED)."""
    # TODO: Implement via AccountStateMachine
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
