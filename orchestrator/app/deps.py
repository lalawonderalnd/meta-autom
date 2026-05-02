"""FastAPI dependencies for auth and database sessions."""

from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .db import get_db

settings = get_settings()
security = HTTPBearer(auto_error=False)


async def verify_jwt(token: str) -> dict | None:
    """Verify a Supabase JWT token."""
    if not settings.SUPABASE_JWT_SECRET:
        # Dev mode - skip verification
        return {"sub": "dev-user"}

    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.PyJWTError:
        return None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict:
    """Get current authenticated user from JWT or API key."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Check for service-to-service API key
    if token == settings.ORCHESTRATOR_API_KEY:
        return {"sub": "service", "role": "service"}

    # Verify JWT
    payload = await verify_jwt(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict | None:
    """Get current user if authenticated, None otherwise."""
    if credentials is None:
        return None

    token = credentials.credentials
    if token == settings.ORCHESTRATOR_API_KEY:
        return {"sub": "service", "role": "service"}

    return await verify_jwt(token)
