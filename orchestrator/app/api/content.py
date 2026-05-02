"""Content management API endpoints."""

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select, func

from accfarm_shared.db_models import ContentItem, Client
from ..config import get_settings
from ..deps import CurrentUser, DbSession

router = APIRouter()
settings = get_settings()


class ContentListResponse(BaseModel):
    """Response for listing content."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


class ContentDetailResponse(BaseModel):
    """Response for content detail."""

    id: str
    client_id: str
    storage_url: str
    content_type: str
    caption: str | None
    hashtag_pool: list[str]
    is_posted: bool
    posted_account_ids: list[str]
    created_at: str


@router.get("", response_model=ContentListResponse)
async def list_content(
    db: DbSession,
    current_user: CurrentUser,
    client_id: str | None = None,
    content_type: str | None = None,
    is_posted: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ContentListResponse:
    """List content items with optional filters."""
    stmt = select(ContentItem)
    
    if client_id:
        stmt = stmt.where(ContentItem.client_id == client_id)
    
    if content_type:
        stmt = stmt.where(ContentItem.content_type == content_type)
    
    if is_posted is not None:
        stmt = stmt.where(ContentItem.is_posted == is_posted)
    
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()
    
    offset = (page - 1) * page_size
    stmt = stmt.order_by(ContentItem.created_at.desc()).offset(offset).limit(page_size)
    
    result = await db.execute(stmt)
    content_items = result.scalars().all()
    
    items = [
        {
            "id": str(item.id),
            "client_id": str(item.client_id),
            "storage_url": item.storage_url,
            "content_type": item.content_type,
            "caption": item.caption,
            "is_posted": item.is_posted,
            "created_at": item.created_at.isoformat(),
        }
        for item in content_items
    ]
    
    return ContentListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{content_id}", response_model=ContentDetailResponse)
async def get_content(db: DbSession, current_user: CurrentUser, content_id: str) -> ContentDetailResponse:
    """Get content item by ID."""
    try:
        content_uuid = uuid.UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content ID")
    
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_uuid))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    return ContentDetailResponse(
        id=str(item.id),
        client_id=str(item.client_id),
        storage_url=item.storage_url,
        content_type=item.content_type,
        caption=item.caption,
        hashtag_pool=item.hashtag_pool,
        is_posted=item.is_posted,
        posted_account_ids=[str(aid) for aid in item.posted_account_ids],
        created_at=item.created_at.isoformat(),
    )


@router.post("")
async def upload_content(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile,
    client_id: str,
    content_type: str | None = None,
    caption: str | None = None,
    hashtags: str | None = None,
) -> dict[str, Any]:
    """Upload content (trigger content ingestion)."""
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")
    
    # Validate client exists
    try:
        client_uuid = uuid.UUID(client_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid client ID")
    
    result = await db.execute(select(Client).where(Client.id == client_uuid))
    client = result.scalar_one_or_none()
    
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
    
    # Determine content type from filename if not provided
    if not content_type:
        ext = Path(file.filename).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            content_type = 'image'
        elif ext in ['.mp4', '.mov', '.avi']:
            content_type = 'reel'
        else:
            content_type = 'image'  # default
    
    # Save file to storage
    storage_path = settings.CONTENT_STORAGE_PATH or "/workspace/content"
    os.makedirs(storage_path, exist_ok=True)
    
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = Path(storage_path) / unique_filename
    
    try:
        content_bytes = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save file: {str(e)}")
    
    # Parse hashtags
    hashtag_pool = []
    if hashtags:
        hashtag_pool = [h.strip() for h in hashtags.split(',') if h.strip()]
    
    # Create content item record
    content_item = ContentItem(
        client_id=client_uuid,
        storage_url=f"file://{file_path}",
        storage_path=str(file_path),
        caption=caption,
        hashtag_pool=hashtag_pool,
        content_type=content_type,
    )
    
    db.add(content_item)
    await db.flush()
    
    return {
        "status": "uploaded",
        "id": str(content_item.id),
        "filename": unique_filename,
        "content_type": content_type,
    }


@router.delete("/{content_id}")
async def delete_content(db: DbSession, current_user: CurrentUser, content_id: str) -> dict[str, Any]:
    """Delete a content item."""
    try:
        content_uuid = uuid.UUID(content_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid content ID")
    
    result = await db.execute(select(ContentItem).where(ContentItem.id == content_uuid))
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content not found")
    
    # Delete file if it exists
    if item.storage_path.startswith('file://'):
        file_path = Path(item.storage_path.replace('file://', ''))
        if file_path.exists():
            os.remove(file_path)
    elif os.path.exists(item.storage_path):
        os.remove(item.storage_path)
    
    await db.delete(item)
    await db.flush()
    
    return {"status": "deleted", "id": content_id}
