import uuid
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import NotFoundError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.models import User

security_scheme = HTTPBearer(auto_error=False)

async def get_user_entity_or_404(
    db: AsyncSession,
    model: type[Any],
    entity_id: uuid.UUID,
    user_id: uuid.UUID,
    error_message: str | None = None,
    options: list[Any] | None = None,
) -> Any:
    """Fetches an entity owned by user_id or raises NotFoundError (IDOR protection)."""
    stmt = select(model).where(and_(model.id == entity_id, model.user_id == user_id))
    if options:
        stmt = stmt.options(*options)
    entity = (await db.execute(stmt)).scalar_one_or_none()
    if not entity:
        raise NotFoundError(error_message or f"{model.__name__} not found")
    return entity

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedError("Authentication credentials missing")
    
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError("Invalid token payload")
    
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError("Invalid user ID in token")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise UnauthorizedError("User no longer exists")
    
    request.state.user = user
    return user
