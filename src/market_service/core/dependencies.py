"""FastAPI dependency injection — database sessions and stateless JWT authentication."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .database import AsyncSessionFactory
from .exceptions import UnauthorizedException
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class CurrentUser(BaseModel):
    user_id: uuid.UUID
    sub: str


async def get_db() -> AsyncGenerator[AsyncSession]:
    """Yield one async database session per request."""

    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> CurrentUser:
    """Extract authenticated user claims statelessly from a valid JWT access token."""

    if not token:
        raise UnauthorizedException("Could not validate credentials")

    payload = decode_access_token(token)

    if payload is None:
        raise UnauthorizedException("Could not validate credentials")

    user_id = payload.get("sub")

    if user_id is None:
        raise UnauthorizedException("Could not validate credentials")

    try:
        uid = uuid.UUID(str(user_id))
    except (ValueError, TypeError):
        raise UnauthorizedException("Could not validate credentials") from None

    return CurrentUser(user_id=uid, sub=str(user_id))


DbDep = Annotated[AsyncSession, Depends(get_db)]
CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
