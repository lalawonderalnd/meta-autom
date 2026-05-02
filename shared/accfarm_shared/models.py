"""Pydantic models for API responses and internal data transfer."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from accfarm_shared.enums import (
    AccountStatus,
    DeviceStatus,
    JobStatus,
    JobKind,
    Platform,
)


class Account(BaseModel):
    """Instagram account model."""

    id: UUID
    platform: Platform = Platform.INSTAGRAM
    username: str
    package_name: str
    device_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    status: AccountStatus = AccountStatus.NEW
    warmup_day: int = 0
    posts_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    proxy_id: Optional[UUID] = None
    identity: dict[str, Any] = Field(default_factory=dict)
    bio: Optional[str] = None
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    last_session_at: Optional[datetime] = None
    last_health_check_at: Optional[datetime] = None
    health_score: float = Field(default=1.0, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Device(BaseModel):
    """Physical Android phone model."""

    id: UUID
    serial: str
    name: str
    ip_address: Optional[str] = None
    adb_port: int = 5555
    android_version: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    status: DeviceStatus = DeviceStatus.OFFLINE
    max_clones: int = 15
    current_clone_count: int = 0
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Proxy(BaseModel):
    """Sticky residential mobile proxy model."""

    id: UUID
    provider: str
    protocol: str  # 'http' or 'socks5'
    host: str
    port: int
    username: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    carrier: Optional[str] = None
    sticky_session_id: Optional[str] = None
    last_ip: Optional[str] = None
    last_ip_check_at: Optional[datetime] = None
    is_alive: bool = True
    bandwidth_used_mb: float = 0.0
    account_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Client(BaseModel):
    """Creator/client whose content we're amplifying."""

    id: UUID
    name: str
    slug: str
    link_in_bio: Optional[str] = None
    niche: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    """Work unit dispatched by the orchestrator."""

    id: UUID
    kind: JobKind
    account_id: Optional[UUID] = None
    device_id: Optional[UUID] = None
    status: JobStatus = JobStatus.QUEUED
    priority: int = Field(default=5, ge=1, le=9)
    payload: dict[str, Any] = Field(default_factory=dict)
    result: Optional[dict[str, Any]] = None
    scheduled_for: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    attempt: int = 0
    max_attempts: int = 3
    error_message: Optional[str] = None
    celery_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """A single bot session (one app launch → close cycle)."""

    id: UUID
    account_id: UUID
    job_id: Optional[UUID] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    ig_app_version: Optional[str] = None
    actions_summary: dict[str, int] = Field(default_factory=dict)
    ended_reason: Optional[str] = None  # 'completed', 'checkpoint', 'crash', 'killswitch'
    ended_with_warning: bool = False


class Action(BaseModel):
    """Individual atomic action within a session."""

    id: UUID
    session_id: UUID
    kind: str  # 'like', 'follow', 'scroll', 'view_story', 'post'
    target: Optional[str] = None  # username/hashtag/post_id
    success: bool
    duration_ms: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=datetime.utcnow)


class ContentItem(BaseModel):
    """Content ready to post (video/image)."""

    id: UUID
    client_id: UUID
    storage_url: str
    storage_path: str
    caption: Optional[str] = None
    hashtag_pool: list[str] = Field(default_factory=list)
    content_type: str  # 'image', 'reel', 'story'
    width: Optional[int] = None
    height: Optional[int] = None
    duration_seconds: Optional[float] = None
    is_posted: bool = False
    posted_account_ids: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
