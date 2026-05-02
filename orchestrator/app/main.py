"""FastAPI application entry point for the Meta Autom Orchestrator."""

import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db, async_session_factory
from .api import accounts, devices, jobs, content, ws
from .workers.celery_app import celery_app

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - startup and shutdown events."""
    # Startup
    logger.info("Starting up orchestrator...")
    
    # Initialize database tables
    await init_db()
    logger.info("Database initialized")
    
    # Start Celery worker tasks (if running in same process)
    # In production, workers run separately
    
    logger.info("Orchestrator startup complete")
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator...")
    # Cleanup: close DB connections, stop background tasks
    await async_session_factory.kwbind().close()
    logger.info("Orchestrator shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.APP_NAME,
        description="Meta Autom Farm Orchestrator API - Manages devices, accounts, jobs, and content",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    
    # CORS middleware for dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(accounts.router, prefix="/api/v1/accounts", tags=["accounts"])
    app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
    app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
    app.include_router(content.router, prefix="/api/v1/content", tags=["content"])
    app.include_router(ws.router, prefix="/api/v1/ws", tags=["websocket"])
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        return {"status": "healthy", "service": "orchestrator"}
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
