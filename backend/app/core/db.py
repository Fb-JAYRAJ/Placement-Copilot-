import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from sqlalchemy import DateTime, Uuid, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.config import settings

logger = logging.getLogger("placement_copilot.db")

# Neon serverless PgBouncer requires prepare_threshold=None
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"prepare_threshold": None},
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=2,
    pool_recycle=300,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

class BaseModel(Base):
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

async def check_db_connection_with_retry(max_retries: int = 3, backoff_sec: float = 1.0) -> bool:
    """Handles Neon cold starts when compute is sleeping."""
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1;"))
                return True
        except Exception as e:
            logger.warning(f"DB connection attempt {attempt} failed: {e}. Retrying in {backoff_sec}s...")
            if attempt == max_retries:
                raise
            await asyncio.sleep(backoff_sec)
            backoff_sec *= 1.5
    return False

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
