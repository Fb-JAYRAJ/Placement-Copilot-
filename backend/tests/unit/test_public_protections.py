import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.errors import RateLimitError
from app.core.ratelimit import check_and_increment_llm_quota
from app.main import app
from app.models.models import LLMUsage, User

# ============================================================================
# 1. ALLOW_SIGNUP Flag Tests
# ============================================================================

@pytest.mark.asyncio
async def test_allow_signup_flag_false_returns_403():
    """When ALLOW_SIGNUP=False, POST /api/v1/auth/register must return 403 Forbidden."""
    with patch.object(settings, "ALLOW_SIGNUP", False):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post("/api/v1/auth/register", json={
                "email": "newuser@example.com",
                "name": "New Candidate",
                "password": "ValidPassword123!",
            })
            assert res.status_code == 403
            data = res.json()
            assert data["error"]["code"] == "FORBIDDEN"
            assert "registration is currently disabled" in data["error"]["message"]


@pytest.mark.asyncio
async def test_allow_signup_flag_defaults_true():
    """Default configuration must have ALLOW_SIGNUP=True."""
    assert settings.ALLOW_SIGNUP is True


# ============================================================================
# 2. Demo Account Safety Guards
# ============================================================================

def make_mock_user(email: str = "demo@placementcopilot.com") -> User:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.email = email
    u.name = "Demo Candidate"
    u.password_hash = "mock_hash"
    return u


@pytest.mark.asyncio
async def test_demo_user_cannot_change_password():
    """Demo user must be rejected with 403 when attempting to change password."""
    demo_user = make_mock_user(settings.DEMO_EMAIL)
    app.dependency_overrides[get_current_user] = lambda: demo_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.post("/api/v1/users/me/password", json={
                "current_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            })
            assert res.status_code == 403
            assert "Demo account password cannot be modified" in res.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_demo_user_cannot_delete_account():
    """Demo user must be rejected with 403 when attempting account deletion."""
    demo_user = make_mock_user(settings.DEMO_EMAIL)
    app.dependency_overrides[get_current_user] = lambda: demo_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.delete("/api/v1/users/me")
            assert res.status_code == 403
            assert "Demo account cannot be deleted" in res.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_demo_user_cannot_export_data():
    """Demo user must be rejected with 403 when attempting data export."""
    demo_user = make_mock_user(settings.DEMO_EMAIL)
    app.dependency_overrides[get_current_user] = lambda: demo_user

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/api/v1/users/me/export")
            assert res.status_code == 403
            assert "Demo account data export is disabled" in res.json()["error"]["message"]
    finally:
        app.dependency_overrides.clear()


# ============================================================================
# 3. Global and Per-User LLM Limits
# ============================================================================

@pytest.mark.asyncio
async def test_global_llm_limit_exhausted_raises_429():
    """When global daily usage hits LLM_GLOBAL_DAILY_LIMIT, check_and_increment_llm_quota raises RateLimitError."""
    mock_db = AsyncMock()

    # Return sum >= LLM_GLOBAL_DAILY_LIMIT
    mock_scalar = MagicMock()
    mock_scalar.scalar.return_value = settings.LLM_GLOBAL_DAILY_LIMIT
    mock_db.execute.return_value = mock_scalar

    user_id = uuid.uuid4()
    with pytest.raises(RateLimitError) as exc_info:
        await check_and_increment_llm_quota(user_id, mock_db)

    assert exc_info.value.status_code == 429
    assert "Global daily LLM limit" in exc_info.value.message


@pytest.mark.asyncio
async def test_demo_user_smaller_llm_quota():
    """Demo user must be limited to DEMO_LLM_DAILY_QUOTA (default 15)."""
    mock_db = AsyncMock()

    # 1. Global check returns 0
    # 2. User query returns demo user
    # 3. Usage query returns usage.calls == DEMO_LLM_DAILY_QUOTA
    demo_user = make_mock_user(settings.DEMO_EMAIL)
    demo_usage = MagicMock(spec=LLMUsage)
    demo_usage.calls = settings.DEMO_LLM_DAILY_QUOTA
    demo_usage.day = date.today()

    res_global = MagicMock()
    res_global.scalar.return_value = 50  # well below 300

    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = demo_user

    res_usage = MagicMock()
    res_usage.scalar_one_or_none.return_value = demo_usage

    mock_db.execute.side_effect = [res_global, res_user, res_usage]

    with pytest.raises(RateLimitError) as exc_info:
        await check_and_increment_llm_quota(demo_user.id, mock_db)

    assert exc_info.value.status_code == 429
    assert f"Demo account daily LLM quota of {settings.DEMO_LLM_DAILY_QUOTA}" in exc_info.value.message


@pytest.mark.asyncio
async def test_regular_user_llm_quota_enforced():
    """Regular user must be limited to LLM_DAILY_QUOTA (default 40)."""
    mock_db = AsyncMock()

    regular_user = make_mock_user("regular@university.edu")
    usage = MagicMock(spec=LLMUsage)
    usage.calls = settings.LLM_DAILY_QUOTA
    usage.day = date.today()

    res_global = MagicMock()
    res_global.scalar.return_value = 50

    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = regular_user

    res_usage = MagicMock()
    res_usage.scalar_one_or_none.return_value = usage

    mock_db.execute.side_effect = [res_global, res_user, res_usage]

    with pytest.raises(RateLimitError) as exc_info:
        await check_and_increment_llm_quota(regular_user.id, mock_db)

    assert exc_info.value.status_code == 429
    assert f"Daily LLM quota of {settings.LLM_DAILY_QUOTA}" in exc_info.value.message


@pytest.mark.asyncio
async def test_llm_quota_increments_when_under_limit():
    """When under limits, calls counter must be incremented and committed."""
    mock_db = AsyncMock()

    regular_user = make_mock_user("candidate@university.edu")
    usage = MagicMock(spec=LLMUsage)
    usage.calls = 5
    usage.day = date.today()

    res_global = MagicMock()
    res_global.scalar.return_value = 50

    res_user = MagicMock()
    res_user.scalar_one_or_none.return_value = regular_user

    res_usage = MagicMock()
    res_usage.scalar_one_or_none.return_value = usage

    mock_db.execute.side_effect = [res_global, res_user, res_usage]

    new_count = await check_and_increment_llm_quota(regular_user.id, mock_db)
    assert new_count == 6
    assert usage.calls == 6
    mock_db.commit.assert_awaited_once()


# ============================================================================
# 4. Registration Rate Limit Configuration
# ============================================================================

def test_registration_rate_limit_setting_defaults():
    assert settings.REGISTER_RATE_LIMIT == "5/hour"
    assert settings.LLM_GLOBAL_DAILY_LIMIT == 300
    assert settings.DEMO_LLM_DAILY_QUOTA == 15
    assert settings.DEMO_EMAIL == "demo@placementcopilot.com"
