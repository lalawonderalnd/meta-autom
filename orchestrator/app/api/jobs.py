"""Job management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func

from accfarm_shared.db_models import Job, Account
from accfarm_shared.enums import JobStatus
from ..deps import CurrentUser, DbSession

router = APIRouter()


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class JobDetailResponse(BaseModel):
    """Response for job detail."""

    id: str
    kind: str
    status: str
    account_id: str | None
    device_id: str | None
    priority: int
    scheduled_for: str
    started_at: str | None
    finished_at: str | None
    attempt: int
    error_message: str | None
    created_at: str


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
    stmt = select(Job)
    
    if status_filter:
        try:
            status_enum = JobStatus(status_filter.upper())
            stmt = stmt.where(Job.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
    if account_id:
        stmt = stmt.where(Job.account_id == account_id)
    
    if device_id:
        stmt = stmt.where(Job.device_id == device_id)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Job.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    
    items = [
        {
            "id": str(job.id),
            "kind": job.kind.value,
            "status": job.status.value,
            "account_id": str(job.account_id) if job.account_id else None,
            "priority": job.priority,
            "scheduled_for": job.scheduled_for.isoformat(),
            "created_at": job.created_at.isoformat(),
        }
        for job in jobs
    ]
    
    return JobListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job(db: DbSession, current_user: CurrentUser, job_id: UUID) -> JobDetailResponse:
    """Get job by ID."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    
    return JobDetailResponse(
        id=str(job.id),
        kind=job.kind.value,
        status=job.status.value,
        account_id=str(job.account_id) if job.account_id else None,
        device_id=str(job.device_id) if job.device_id else None,
        priority=job.priority,
        scheduled_for=job.scheduled_for.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        attempt=job.attempt,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
    )


@router.delete("/{job_id}")
async def cancel_job(
    db: DbSession,
    current_user: CurrentUser,
    job_id: UUID,
) -> dict[str, Any]:
    """Cancel a queued job."""
    from ..services.job_dispatcher import JobDispatcher
    
    dispatcher = JobDispatcher(db)
    result = await dispatcher.cancel_job(job_id)
    
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or already completed")
    
    return {"status": "cancelled", "job_id": str(job_id)}


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
