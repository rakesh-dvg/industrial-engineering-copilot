"""FastAPI dependencies for authentication (Phase 1 foundation)."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.interfaces import AuthContext, AuthenticatedUser, OrganizationContext
from app.database import get_db_session

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_optional_auth_context() -> AuthContext | None:
    """Return authenticated context when JWT auth is implemented."""
    return None


async def get_current_user(
    auth_context: Annotated[AuthContext | None, Depends(get_optional_auth_context)],
) -> AuthenticatedUser:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "AUTH_NOT_IMPLEMENTED",
                "message": "Authentication is not implemented in Phase 1.",
                "details": {},
            }
        },
    )


async def get_organization_context(
    auth_context: Annotated[AuthContext | None, Depends(get_optional_auth_context)],
) -> OrganizationContext:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": {
                "code": "AUTH_NOT_IMPLEMENTED",
                "message": "Organization context requires authentication.",
                "details": {},
            }
        },
    )
