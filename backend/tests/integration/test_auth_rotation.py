import asyncio
from datetime import UTC, datetime, timedelta
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_refresh_token
from app.models.models import RefreshToken


@pytest.mark.asyncio
async def test_auth_rotation_normal_and_grace_window(client: AsyncClient, db_session: AsyncSession):
    # 1. Create a user via registration
    email = f"rotation_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Rotation Tester",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    initial_cookie = reg_res.cookies.get("refresh_token")
    assert initial_cookie is not None

    # 2. Normal rotation: Refresh with initial token
    headers_initial = {"Cookie": f"refresh_token={initial_cookie}"}
    ref_res1 = await client.post("/api/v1/auth/refresh", headers=headers_initial)
    assert ref_res1.status_code == 200
    successor_cookie = ref_res1.cookies.get("refresh_token")
    assert successor_cookie is not None
    assert successor_cookie != initial_cookie

    # 3. Within grace window (10s): Concurrent/subsequent call with the SAME initial token
    ref_res2 = await client.post("/api/v1/auth/refresh", headers=headers_initial)
    assert ref_res2.status_code == 200
    reused_cookie = ref_res2.cookies.get("refresh_token")
    # Must return the EXACT SAME successor!
    assert reused_cookie == successor_cookie

    # 4. Successor token itself works normally
    headers_successor = {"Cookie": f"refresh_token={successor_cookie}"}
    ref_res3 = await client.post("/api/v1/auth/refresh", headers=headers_successor)
    assert ref_res3.status_code == 200
    third_cookie = ref_res3.cookies.get("refresh_token")
    assert third_cookie is not None
    assert third_cookie != successor_cookie


@pytest.mark.asyncio
async def test_auth_concurrent_refreshes_same_token(client: AsyncClient):
    # Register candidate
    email = f"concurrent_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Concurrent Tester",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    raw_token = reg_res.cookies.get("refresh_token")
    assert raw_token is not None

    headers = {"Cookie": f"refresh_token={raw_token}"}

    # Run two concurrent refreshes with the exact same initial token
    res1, res2 = await asyncio.gather(
        client.post("/api/v1/auth/refresh", headers=headers),
        client.post("/api/v1/auth/refresh", headers=headers),
    )

    assert res1.status_code == 200
    assert res2.status_code == 200

    cookie1 = res1.cookies.get("refresh_token")
    cookie2 = res2.cookies.get("refresh_token")
    assert cookie1 is not None
    assert cookie2 is not None
    # Both concurrent calls return the exact same successor token!
    assert cookie1 == cookie2


@pytest.mark.asyncio
async def test_auth_reuse_after_grace_window_revokes_family(client: AsyncClient, db_session: AsyncSession):
    # Register candidate
    email = f"family_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Family Tester",
            "password": "Password123!",
        },
    )
    assert reg_res.status_code == 201
    old_raw_token = reg_res.cookies.get("refresh_token")
    assert old_raw_token is not None

    # Rotate old token to new token
    headers_old = {"Cookie": f"refresh_token={old_raw_token}"}
    ref_res = await client.post("/api/v1/auth/refresh", headers=headers_old)
    assert ref_res.status_code == 200
    new_raw_token = ref_res.cookies.get("refresh_token")
    assert new_raw_token is not None

    # Manually backdate revoked_at of the old token in the database to 30 seconds ago
    old_hash = hash_refresh_token(old_raw_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == old_hash)
    record = (await db_session.execute(stmt)).scalar_one()
    record.revoked_at = datetime.now(UTC) - timedelta(seconds=30)
    await db_session.commit()

    # Attempt to reuse the old token after the grace window (30s > 10s)
    reuse_res = await client.post("/api/v1/auth/refresh", headers=headers_old)
    # Must be rejected with 401 Unauthorized
    assert reuse_res.status_code == 401

    # Entire family should now be revoked, so the successor token should also be rejected!
    headers_new = {"Cookie": f"refresh_token={new_raw_token}"}
    successor_res = await client.post("/api/v1/auth/refresh", headers=headers_new)
    assert successor_res.status_code == 401
