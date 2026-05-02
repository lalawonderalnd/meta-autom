"""API router initialization."""

from fastapi import APIRouter

from . import accounts, content, devices, jobs, ws

api_router = APIRouter()

api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(ws.router, prefix="/ws", tags=["websocket"])
