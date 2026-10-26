import uuid
from datetime import date

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import RateLimitError


def get_rate_limit_key(request: Request) -> str:
    # If user is authenticated, use user ID, else client IP
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return f"user:{user.id}"
    return get_remote_address(request)

limiter = Limiter(key_func=get_rate_limit_key)

async def check_and_increment_llm_quota(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Checks and increments daily LLM calls for user in llm_usage table."""
    # Local import to prevent circular dependency
    from app.models.models import LLMUsage

    today = date.today()
    stmt = select(LLMUsage).where(LLMUsage.user_id == user_id, LLMUsage.day == today)
    result = await db.execute(stmt)
    usage = result.scalar_one_or_none()

    if usage is None:
        usage = LLMUsage(user_id=user_id, day=today, calls=1)
        db.add(usage)
        await db.commit()
        return 1
    
    if usage.calls >= settings.LLM_DAILY_QUOTA:
        raise RateLimitError(
            f"Daily LLM quota of {settings.LLM_DAILY_QUOTA} calls exceeded. Resets at midnight UTC."
        )
    
    usage.calls += 1
    await db.commit()
    return usage.calls
