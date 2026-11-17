import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cross_user_idor_authorization_and_pagination(client: AsyncClient):
    # 1. Register User A
    uid_a = uuid.uuid4().hex[:8]
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_a_{uid_a}@example.com",
            "name": "User Alpha",
            "password": "Password123!",
        },
    )
    assert res_a.status_code == 201
    headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

    # 2. Register User B
    uid_b = uuid.uuid4().hex[:8]
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_b_{uid_b}@example.com",
            "name": "User Beta",
            "password": "Password123!",
        },
    )
    assert res_b.status_code == 201
    headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # 3. User A creates resources
    # 3a. Resume
    resume_resp = await client.post(
        "/api/v1/resumes",
        data={"content_text": "Experienced Python Backend Engineer with FastAPI, Docker, and PostgreSQL expertise."},
        headers=headers_a,
    )
    assert resume_resp.status_code == 201
    resume_id = resume_resp.json()["id"]

    # 3b. Job Description
    jd_resp = await client.post(
        "/api/v1/job-descriptions",
        json={
            "company": "Alpha Corp",
            "role": "Senior Engineer",
            "jd_text": "Looking for Senior Backend Developer with Python and FastAPI experience.",
        },
        headers=headers_a,
    )
    assert jd_resp.status_code == 201
    jd_id = jd_resp.json()["id"]

    # 3c. ATS Analysis
    ats_resp = await client.post(
        "/api/v1/ats/analyze",
        json={"resume_id": resume_id, "jd_id": jd_id},
        headers=headers_a,
    )
    assert ats_resp.status_code == 201
    analysis_id = ats_resp.json()["id"]

    # 3d. DSA Attempt
    topics_resp = await client.get("/api/v1/dsa/topics", headers=headers_a)
    assert topics_resp.status_code == 200
    topic_id = topics_resp.json()["items"][0]["id"]

    problems_resp = await client.get("/api/v1/dsa/problems?limit=1", headers=headers_a)
    assert problems_resp.status_code == 200
    p_item = problems_resp.json()["items"][0]

    attempt_resp = await client.post(
        "/api/v1/dsa/attempts",
        json={
            "problem_id": p_item["id"],
            "topic_id": topic_id,
            "difficulty": "medium",
            "status": "solved",
            "confidence": 4,
            "time_spent_min": 25,
            "notes": "Hash map two pass",
        },
        headers=headers_a,
    )
    assert attempt_resp.status_code == 201
    attempt_id = attempt_resp.json()["id"]

    # 3e. Mock Interview
    interview_resp = await client.post(
        "/api/v1/interviews",
        json={"track": "dsa_concepts", "company": "Alpha Corp", "role": "Senior Engineer", "planned_questions": 3},
        headers=headers_a,
    )
    assert interview_resp.status_code == 201
    interview_id = interview_resp.json()["id"]
    question_id = interview_resp.json()["current_question"]["id"]

    # 4. Proving User B CANNOT read, update, delete, or reference User A's resources
    # Resume IDOR
    assert (await client.get(f"/api/v1/resumes/{resume_id}", headers=headers_b)).status_code == 404
    assert (await client.delete(f"/api/v1/resumes/{resume_id}", headers=headers_b)).status_code == 404

    # Job Description IDOR
    assert (await client.get(f"/api/v1/job-descriptions/{jd_id}", headers=headers_b)).status_code == 404

    # ATS Analysis IDOR
    assert (await client.get(f"/api/v1/ats/analyses/{analysis_id}", headers=headers_b)).status_code == 404
    # User B cannot analyze using User A's resume or JD
    assert (
        await client.post(
            "/api/v1/ats/analyze",
            json={"resume_id": resume_id, "inline_jd_text": "Some JD text requiring python"},
            headers=headers_b,
        )
    ).status_code == 404
    assert (
        await client.post(
            "/api/v1/ats/analyze",
            json={"resume_id": str(uuid.uuid4()), "jd_id": jd_id},
            headers=headers_b,
        )
    ).status_code == 404

    # DSA Attempt IDOR
    assert (
        await client.patch(
            f"/api/v1/dsa/attempts/{attempt_id}",
            json={"notes": "Malicious overwrite"},
            headers=headers_b,
        )
    ).status_code == 404
    assert (await client.delete(f"/api/v1/dsa/attempts/{attempt_id}", headers=headers_b)).status_code == 404

    # Interview IDOR
    assert (await client.get(f"/api/v1/interviews/{interview_id}", headers=headers_b)).status_code == 404
    assert (
        await client.post(
            f"/api/v1/interviews/{interview_id}/answers",
            json={"question_id": question_id, "answer_text": "Unauthorized answer"},
            headers=headers_b,
        )
    ).status_code == 404
    assert (
        await client.post(
            f"/api/v1/interviews/{interview_id}/follow-up?question_id={question_id}",
            headers=headers_b,
        )
    ).status_code == 404
    assert (await client.post(f"/api/v1/interviews/{interview_id}/finish", headers=headers_b)).status_code == 404
    assert (await client.get(f"/api/v1/interviews/{interview_id}/report", headers=headers_b)).status_code == 404

    # 5. Data Export Isolation: User B export contains zero of User A's items
    export_b = await client.get("/api/v1/users/me/export", headers=headers_b)
    assert export_b.status_code == 200
    export_data = export_b.json()
    assert export_data["user"]["email"] == f"user_b_{uid_b}@example.com"
    assert len(export_data["resumes"]) == 0
    assert len(export_data["job_descriptions"]) == 0
    assert len(export_data["ats_analyses"]) == 0
    assert len(export_data["dsa_attempts"]) == 0
    assert len(export_data["mock_interviews"]) == 0

    # 6. Pagination limits capped at 100 (rejecting >100 with 422)
    assert (await client.get("/api/v1/resumes?limit=101", headers=headers_a)).status_code == 422
    assert (await client.get("/api/v1/job-descriptions?limit=101", headers=headers_a)).status_code == 422
    assert (await client.get("/api/v1/ats/analyses?limit=101", headers=headers_a)).status_code == 422
    assert (await client.get("/api/v1/interviews?limit=101", headers=headers_a)).status_code == 422
    assert (await client.get("/api/v1/dsa/attempts?limit=101", headers=headers_a)).status_code == 422
    assert (await client.get("/api/v1/dashboard/readiness/history?limit=101", headers=headers_a)).status_code == 422
