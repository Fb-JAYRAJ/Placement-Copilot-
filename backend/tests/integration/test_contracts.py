import uuid

import pytest
from httpx import AsyncClient

from scripts.seed import run_seed


def assert_paginated_envelope(data: dict):
    """Asserts that a JSON response complies with the PaginatedResponse[T] envelope."""
    assert isinstance(data, dict), f"Expected dict envelope, got {type(data)}"
    assert "items" in data, f"Missing 'items' in envelope keys: {list(data.keys())}"
    assert "total" in data, f"Missing 'total' in envelope keys: {list(data.keys())}"
    assert "limit" in data, f"Missing 'limit' in envelope keys: {list(data.keys())}"
    assert "offset" in data, f"Missing 'offset' in envelope keys: {list(data.keys())}"
    assert isinstance(data["items"], list), f"Expected list in 'items', got {type(data['items'])}"
    assert isinstance(data["total"], int), f"Expected int in 'total', got {type(data['total'])}"
    assert isinstance(data["limit"], int), f"Expected int in 'limit', got {type(data['limit'])}"
    assert isinstance(data["offset"], int), f"Expected int in 'offset', got {type(data['offset'])}"


@pytest.mark.asyncio
async def test_all_list_endpoints_contract(client: AsyncClient, db_session):
    """Validates that every REST list endpoint strictly enforces the PaginatedResponse schema."""
    await run_seed(session=db_session)

    # Register and authenticate candidate
    email = f"contract_test_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "Contract Candidate",
        "password": "Password123!",
        "college": "Test University",
        "grad_year": 2026,
        "target_role": "Backend Engineer",
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /dsa/topics
    res = await client.get("/api/v1/dsa/topics", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 2. GET /dsa/problems
    res = await client.get("/api/v1/dsa/problems", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 3. GET /dsa/attempts
    res = await client.get("/api/v1/dsa/attempts", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 4. GET /dsa/mastery
    res = await client.get("/api/v1/dsa/mastery", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 5. GET /dsa/recommendations
    res = await client.get("/api/v1/dsa/recommendations", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 6. GET /dsa/reviews/due
    res = await client.get("/api/v1/dsa/reviews/due", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 7. GET /resumes
    res = await client.get("/api/v1/resumes", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 8. GET /job-descriptions
    res = await client.get("/api/v1/job-descriptions", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 9. GET /ats/analyses
    res = await client.get("/api/v1/ats/analyses", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 10. GET /interviews
    res = await client.get("/api/v1/interviews", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())

    # 11. GET /dashboard/readiness/history
    res = await client.get("/api/v1/dashboard/readiness/history", headers=headers)
    assert res.status_code == 200
    assert_paginated_envelope(res.json())


@pytest.mark.asyncio
async def test_detail_and_summary_endpoints_contract(client: AsyncClient, db_session):
    """Validates response shapes for detail, summary, and action routes."""
    await run_seed(session=db_session)

    email = f"contract_detail_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "Contract Detail Candidate",
        "password": "Password123!",
    })
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /users/me
    me_res = await client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert isinstance(me_data, dict)
    assert {"id", "email", "name", "created_at"}.issubset(set(me_data.keys()))

    # 2. GET /dsa/stats
    stats_res = await client.get("/api/v1/dsa/stats", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert isinstance(stats_data, dict)
    assert {"total_solved", "total_attempts", "current_streak", "solved_7d"}.issubset(set(stats_data.keys()))

    # 3. GET /dashboard/summary
    dash_res = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert isinstance(dash_data, dict)
    assert {"composite", "confidence", "has_enough_data", "components", "weights", "levers"}.issubset(set(dash_data.keys()))

    # 4. GET /users/me/export
    export_res = await client.get("/api/v1/users/me/export", headers=headers)
    assert export_res.status_code == 200
    export_data = export_res.json()
    assert isinstance(export_data, dict)
    assert {"user", "dsa_attempts", "resumes", "mock_interviews", "ats_analyses"}.issubset(set(export_data.keys()))

    # 5. POST & GET /interviews/{id}
    start_res = await client.post("/api/v1/interviews", json={
        "track": "dsa_concepts",
        "company": "Google",
        "role": "Software Engineer",
        "planned_questions": 3,
    }, headers=headers)
    assert start_res.status_code == 201
    interview_id = start_res.json()["id"]

    detail_res = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert isinstance(detail_data, dict)
    assert {"id", "track", "status", "current_question"}.issubset(set(detail_data.keys()))
