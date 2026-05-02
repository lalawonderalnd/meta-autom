"""Device management API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func

from accfarm_shared.db_models import Device, Account, Session
from accfarm_shared.enums import DeviceStatus
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
    name: str
    ip_address: str | None
    model: str
    manufacturer: str | None
    android_version: str | None
    status: str
    max_clones: int
    current_clone_count: int
    current_sessions: list[dict[str, Any]]
    last_heartbeat: str | None
    created_at: str
    updated_at: str


class RegisterDeviceRequest(BaseModel):
    """Request to register a new device."""

    serial: str
    name: str
    ip_address: str | None = None
    adb_port: int = 5555
    model: str | None = None
    manufacturer: str | None = None
    android_version: str | None = None
    max_clones: int = 15


@router.get("", response_model=DeviceListResponse)
async def list_devices(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> DeviceListResponse:
    """List devices with optional filters."""
    stmt = select(Device)
    
    if status_filter:
        try:
            status_enum = DeviceStatus(status_filter.upper())
            stmt = stmt.where(Device.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    offset = (page - 1) * page_size
    stmt = stmt.order_by(Device.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    devices = result.scalars().all()
    
    items = [
        {
            "id": str(dev.id),
            "serial": dev.serial,
            "name": dev.name,
            "status": dev.status.value,
            "current_clone_count": dev.current_clone_count,
            "max_clones": dev.max_clones,
            "last_heartbeat": dev.last_heartbeat.isoformat() if dev.last_heartbeat else None,
            "created_at": dev.created_at.isoformat(),
        }
        for dev in devices
    ]
    
    return DeviceListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(db: DbSession, current_user: CurrentUser, device_id: UUID) -> DeviceDetailResponse:
    """Get device by ID with current sessions."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    
    # Get current active sessions (accounts on this device with recent activity)
    accounts_result = await db.execute(
        select(Account)
        .where(Account.device_id == device_id)
        .limit(10)
    )
    accounts = accounts_result.scalars().all()
    
    current_sessions = [
        {
            "account_id": str(acc.id),
            "username": acc.username,
            "status": acc.status.value,
        }
        for acc in accounts
    ]
    
    return DeviceDetailResponse(
        id=str(device.id),
        serial=device.serial,
        name=device.name,
        ip_address=device.ip_address,
        model=device.model or "Unknown",
        manufacturer=device.manufacturer,
        android_version=device.android_version,
        status=device.status.value,
        max_clones=device.max_clones,
        current_clone_count=device.current_clone_count,
        current_sessions=current_sessions,
        last_heartbeat=device.last_heartbeat.isoformat() if device.last_heartbeat else None,
        created_at=device.created_at.isoformat(),
        updated_at=device.updated_at.isoformat(),
    )


@router.post("")
async def register_device(
    db: DbSession,
    current_user: CurrentUser,
    request: RegisterDeviceRequest,
) -> dict[str, Any]:
    """Register a new device."""
    # Check if device with this serial already exists
    existing = await db.execute(select(Device).where(Device.serial == request.serial))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device with this serial already exists")
    
    device = Device(
        serial=request.serial,
        name=request.name,
        ip_address=request.ip_address,
        adb_port=request.adb_port,
        model=request.model,
        manufacturer=request.manufacturer,
        android_version=request.android_version,
        max_clones=request.max_clones,
        status=DeviceStatus.ONLINE if request.ip_address else DeviceStatus.OFFLINE,
    )
    
    db.add(device)
    await db.flush()
    
    return {"id": str(device.id), "serial": device.serial, "status": "registered"}


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
