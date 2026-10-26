import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_summary_and_snapshots(client: AsyncClient):
    # 1. Register candidate user
    email = f"dashboard_user_{uuid.uuid4().hex[:8]}@example.com"
    res_auth = await client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "David Candidate",
        "password": "Password123!",
    })
    token = res_auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check fresh dashboard summary (Empty/Onboarding state)
    summary_res = await client.get("/api/v1/dashboard/summary?range=30d", headers=headers)
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["user_name"] == "David"
    assert summary["confidence"] <= 0.2
    assert summary["onboarding_checklist"]["has_uploaded_resume"] is False
    assert summary["onboarding_checklist"]["has_logged_3_problems"] is False
    assert summary["onboarding_checklist"]["has_taken_mock"] is False
    assert len(summary["levers"]) == 3
    assert summary["daily_focus_task"] is not None

    # Sparklines must match requested 30d range
    assert len(summary["ats_sparkline"]) == 30
    assert len(summary["dsa_sparkline"]) == 30
    assert len(summary["mock_sparkline"]) == 30

    # Test 7d range
    summary_7d = await client.get("/api/v1/dashboard/summary?range=7d", headers=headers)
    assert summary_7d.status_code == 200
    assert len(summary_7d.json()["ats_sparkline"]) == 7

    # 3. Add data: Upload a resume
    await client.post(
        "/api/v1/resumes",
        data={"title": "Resume 1", "content_text": "Experienced Python Software Engineer with PostgreSQL and Docker expertise."},
        headers=headers,
    )

    # 4. Re-check summary: onboarding checklist for resume should now be True
    updated_summary = (await client.get("/api/v1/dashboard/summary", headers=headers)).json()
    assert updated_summary["onboarding_checklist"]["has_uploaded_resume"] is True

    # 5. Check readiness history endpoint
    history_res = await client.get("/api/v1/dashboard/readiness/history", headers=headers)
    assert history_res.status_code == 200
    h_data = history_res.json()
    assert "items" in h_data and "total" in h_data
    assert isinstance(h_data["items"], list)
