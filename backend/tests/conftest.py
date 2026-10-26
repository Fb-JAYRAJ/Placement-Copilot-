import os
import sys

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.config import settings
from app.core.db import Base, get_db
from app.core.ratelimit import limiter
from app.main import app
from app.services.llm.provider import FakeProvider, set_llm_provider
from sqlalchemy import text

# Always use FakeProvider in tests
set_llm_provider(FakeProvider())

# Disable rate limiter for tests
limiter.enabled = False

if not settings.TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL must be configured for running tests")

test_db_url = settings.TEST_DATABASE_URL

test_engine = create_async_engine(
    test_db_url,
    connect_args={"prepare_threshold": None},
    pool_pre_ping=True,
)

TestingSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    # Create all tables on the test database
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS family_id UUID DEFAULT gen_random_uuid() NOT NULL;"))
        await conn.execute(text("ALTER TABLE refresh_tokens ADD COLUMN IF NOT EXISTS successor_token VARCHAR(255);"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_refresh_tokens_family_id ON refresh_tokens (family_id);"))
    yield
    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
