"""Device management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from ..deps import CurrentUser, DbSession

router = APIRouter()


class DeviceListResponse(BaseModel):
    """Response for listing devices."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class DeviceDetailResponse(BaseModel):
    """Response for device detail."""

    id: str
    serial: str
    model: str
    status: str
    current_sessions: list[dict[str, Any]]
    last_heartbeat: str | None
    created_at: str


class RegisterDeviceRequest(BaseModel):
    """Request to register a new device."""

    serial: str
    model: str
    proxy_id: str | None = None


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DeviceListResponse:
    """List devices with optional filters."""
    # TODO: Implement
    return DeviceListResponse(items=[], total=0, page=page, page_size=page_size)


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(db: DbSession, current_user: CurrentUser, device_id: UUID) -> DeviceDetailResponse:
    """Get device by ID with current sessions."""
    # TODO: Implement
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")


@router.post("")
async def register_device(
    db: DbSession,
    current_user: CurrentUser,
    request: RegisterDeviceRequest,
) -> dict[str, Any]:
    """Register a new device."""
    # TODO: Implement
    return {"id": "new-device-id", "status": "registered"}


@router.post("/{device_id}/scan")
async def scan_device(
    db: DbSession,
    current_user: CurrentUser,
    device_id: UUID,
) -> dict[str, Any]:
    """Trigger device clone scan + reconnect."""
    # TODO: Implement via DeviceScanner
    from ..services.device_scanner import DeviceScanner

    scanner = DeviceScanner(db)
    try:
        result = await scanner.scan_device(device_id)
        return {"status": "scanned", "clones_found": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{device_id}/killswitch")
async def killswitch_device(
    db: DbSession,
    current_user: CurrentUser,
    device_id: UUID,
) -> dict[str, Any]:
    """Emergency stop - cancel all running jobs on a device."""
    # TODO: Implement
    from ..services.job_dispatcher import JobDispatcher

    dispatcher = JobDispatcher(db)
    try:
        cancelled = await dispatcher.cancel_all_for_device(device_id)
        return {"status": "killed", "cancelled_jobs": cancelled}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{device_id}/stream")
async def get_device_stream(
    db: DbSession,
    current_user: CurrentUser,
    device_id: UUID,
) -> dict[str, str]:
    """Return ws-scrcpy URL for dashboard iframe."""
    # TODO: Implement - returns ws-scrcpy connection URL
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
