import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_auth_full_flow(client: AsyncClient):
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # 1. Register
    reg_payload = {
        "email": unique_email,
        "name": "Alex Candidate",
        "password": password,
        "college": "Stanford",
        "grad_year": 2026,
        "target_role": "Backend Engineer",
        "target_companies": ["Google", "Stripe"],
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, reg_res.text
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == unique_email
    assert data["user"]["name"] == "Alex Candidate"
    assert "refresh_token" in reg_res.cookies

    access_token = data["access_token"]
    refresh_cookie = reg_res.cookies["refresh_token"]

    # 2. Duplicate registration should fail with 409
    dup_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "CONFLICT"

    # 3. Short password validation failure (422)
    short_pw_payload = {
        "email": f"short_{uuid.uuid4().hex[:8]}@example.com",
        "name": "Short PW",
        "password": "short",
    }
    short_res = await client.post("/api/v1/auth/register", json=short_pw_payload)
    assert short_res.status_code == 422

    # 4. Access protected endpoint /users/me
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == unique_email

    # 5. Unauthorized access without token
    unauth_res = await client.get("/api/v1/users/me")
    assert unauth_res.status_code == 401

    # 6. Login with valid credentials
    login_payload = {"email": unique_email, "password": password}
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 7. Login with invalid password
    bad_login_res = await client.post("/api/v1/auth/login", json={"email": unique_email, "password": "WrongPassword123!"})
    assert bad_login_res.status_code == 401

    # 8. Refresh token rotation
    refresh_res = await client.post("/api/v1/auth/refresh", headers={"Cookie": f"refresh_token={refresh_cookie}"})
    assert refresh_res.status_code == 200
    new_data = refresh_res.json()
    assert "access_token" in new_data
    new_refresh_cookie = refresh_res.cookies.get("refresh_token")
    assert new_refresh_cookie is not None

    # Within grace window, immediate reuse returns the same successor
    grace_res = await client.post("/api/v1/auth/refresh", headers={"Cookie": f"refresh_token={refresh_cookie}"})
    assert grace_res.status_code == 200
    assert grace_res.cookies.get("refresh_token") == new_refresh_cookie

    # Invalid refresh token should be rejected (401)
    invalid_res = await client.post("/api/v1/auth/refresh", headers={"Cookie": "refresh_token=invalid_dummy_token"})
    assert invalid_res.status_code == 401

    # 9. Logout
    logout_res = await client.post("/api/v1/auth/logout", headers={"Cookie": f"refresh_token={new_refresh_cookie}"})
    assert logout_res.status_code == 200

    # 10. Health endpoints
    health_res = await client.get("/api/v1/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    db_health_res = await client.get("/api/v1/health/db")
    assert db_health_res.status_code == 200
    assert db_health_res.json()["status"] == "ok"
