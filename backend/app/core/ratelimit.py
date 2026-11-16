import uuid
from datetime import date

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import func, select
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
    """Checks and increments daily LLM calls for user in llm_usage table with global and per-user limits."""
    # Local import to prevent circular dependency
    from app.models.models import LLMUsage, User

    today = date.today()

    # 1. Global daily LLM budget check across all users
    global_stmt = select(func.coalesce(func.sum(LLMUsage.calls), 0)).where(LLMUsage.day == today)
    global_calls = (await db.execute(global_stmt)).scalar() or 0
    if global_calls >= settings.LLM_GLOBAL_DAILY_LIMIT:
        raise RateLimitError(
            f"Global daily LLM limit of {settings.LLM_GLOBAL_DAILY_LIMIT} calls reached across all users. Please try again tomorrow."
        )

    # 2. Determine per-user quota (demo account has lower quota)
    user_stmt = select(User).where(User.id == user_id)
    user = (await db.execute(user_stmt)).scalar_one_or_none()
    is_demo = user and user.email.lower() == settings.DEMO_EMAIL.lower()
    user_quota = settings.DEMO_LLM_DAILY_QUOTA if is_demo else settings.LLM_DAILY_QUOTA

    # 3. User daily quota check & increment
    stmt = select(LLMUsage).where(LLMUsage.user_id == user_id, LLMUsage.day == today)
    result = await db.execute(stmt)
    usage = result.scalar_one_or_none()

    if usage is None:
        usage = LLMUsage(user_id=user_id, day=today, calls=1)
        db.add(usage)
        await db.commit()
        return 1

    if usage.calls >= user_quota:
        user_type = "Demo account daily" if is_demo else "Daily"
        raise RateLimitError(
            f"{user_type} LLM quota of {user_quota} calls exceeded. Resets at midnight UTC."
        )

    usage.calls += 1
    await db.commit()
    return usage.calls
