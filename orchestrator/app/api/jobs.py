"""Job management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from ..deps import CurrentUser, DbSession

router = APIRouter()


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class BulkJobRequest(BaseModel):
    """Request to dispatch bulk jobs."""

    kind: str
    account_ids: list[UUID]
    payload: dict[str, Any] | None = None
    stagger_seconds: int = 30


@router.get("", response_model=JobListResponse)
async def list_jobs(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    account_id: UUID | None = None,
    device_id: UUID | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> JobListResponse:
    """List jobs with optional filters."""
    # TODO: Implement
    return JobListResponse(items=[], total=0, page=page, page_size=page_size)


@router.delete("/{job_id}")
async def cancel_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> dict[str, Any]:
    """Cancel a queued job."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.post("/bulk")
async def dispatch_bulk_jobs(
    db: DbSession,
    current_user: CurrentUser,
    request: BulkJobRequest,
) -> dict[str, Any]:
    """Bulk dispatch jobs with stagger."""
    # TODO: Implement via JobDispatcher
    from ..services.job_dispatcher import JobDispatcher

    dispatcher = JobDispatcher(db)
    try:
        jobs = await dispatcher.dispatch_bulk(
            kind=request.kind,
            account_ids=request.account_ids,
            payload=request.payload,
            stagger_seconds=request.stagger_seconds,
        )
        return {"status": "dispatched", "job_count": len(jobs), "jobs": [str(j.id) for j in jobs]}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
