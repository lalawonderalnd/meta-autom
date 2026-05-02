"""Content management API endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, UploadFile, status
from pydantic import BaseModel

from ..deps import CurrentUser, DbSession

router = APIRouter()


class ContentListResponse(BaseModel):
    """Response for listing content."""

    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int


@router.get("", response_model=ContentListResponse)
async def list_content(
    db: DbSession,
    current_user: CurrentUser,
    kind_filter: str | None = Query(None, alias="kind"),
    niche: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ContentListResponse:
    """List content items with optional filters."""
    # TODO: Implement
    return ContentListListResponse(items=[], total=0, page=page, page_size=page_size)


@router.post("")
async def upload_content(
    db: DbSession,
    current_user: CurrentUser,
    file: UploadFile,
    kind: str | None = None,
    niche: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Upload content (trigger content ingestion)."""
    # TODO: Implement - save file, extract metadata, create content_item row
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No filename provided")

    return {"status": "uploaded", "filename": file.filename}
