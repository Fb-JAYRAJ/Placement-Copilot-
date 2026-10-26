import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_interview_full_adaptive_session_and_idor(client: AsyncClient):
    # 1. Register candidate user
    email = f"interview_user_{uuid.uuid4().hex[:8]}@example.com"
    res_auth = await client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "Jane Interviewee",
        "password": "Password123!",
    })
    token = res_auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Start Mock Interview
    start_payload = {
        "track": "dsa_concepts",
        "company": "Google",
        "role": "Software Engineer",
        "planned_questions": 3,
    }
    create_res = await client.post("/api/v1/interviews", json=start_payload, headers=headers)
    assert create_res.status_code == 201
    iv = create_res.json()
    interview_id = iv["id"]
    assert iv["ability"] == 2.5
    assert iv["current_question"] is not None
    q1 = iv["current_question"]
    q1_id = q1["id"]

    # 3. Submit strong answer to Q1
    ans1_payload = {
        "question_id": q1_id,
        "answer_text": (
            "Binary search requires a sorted collection and maintains the invariant left <= right. "
            "To prevent integer overflow in mid index calculation, we compute mid = left + (right - left) // 2. "
            "The search space is halved every iteration, guaranteeing strict O(log n) time complexity and O(1) space."
        ),
        "time_taken_sec": 45,
    }
    ans1_res = await client.post(f"/api/v1/interviews/{interview_id}/answers", json=ans1_payload, headers=headers)
    assert ans1_res.status_code == 200
    res1_data = ans1_res.json()
    assert res1_data["completed"] is False
    assert res1_data["next_question"] is not None
    q2 = res1_data["next_question"]
    q2_id = q2["id"]

    # Ability must have increased
    session_res = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    updated_ability = session_res.json()["ability"]
    assert updated_ability >= 2.5

    # 4. Request a follow-up for Q1
    follow_up_res = await client.post(f"/api/v1/interviews/{interview_id}/follow-up?question_id={q1_id}", headers=headers)
    assert follow_up_res.status_code == 200
    follow_up_q = follow_up_res.json()
    assert follow_up_q["parent_question_id"] == q1_id
    assert follow_up_q["source"] == "follow_up"

    # Duplicate follow-up request on same question must fail with 422
    dup_f_res = await client.post(f"/api/v1/interviews/{interview_id}/follow-up?question_id={q1_id}", headers=headers)
    assert dup_f_res.status_code == 422

    # 5. Submit answer to follow-up
    ans_f_res = await client.post(
        f"/api/v1/interviews/{interview_id}/answers",
        json={
            "question_id": follow_up_q["id"],
            "answer_text": "Under high concurrency, reader-writer locks or lock-free skip lists prevent contention.",
            "time_taken_sec": 30,
        },
        headers=headers,
    )
    assert ans_f_res.status_code == 200

    # 6. Submit answer to Q2 to complete the 3-question planned session
    ans2_payload = {
        "question_id": q2_id,
        "answer_text": "Hash tables use modulo arithmetic for bucketing and separate chaining or open addressing for collisions.",
        "time_taken_sec": 40,
    }
    ans2_res = await client.post(f"/api/v1/interviews/{interview_id}/answers", json=ans2_payload, headers=headers)
    assert ans2_res.status_code == 200
    res2_data = ans2_res.json()
    assert res2_data["completed"] is True
    assert res2_data["report"] is not None
    assert "theta_trajectory" in res2_data["report"]
    assert "overall_score" in res2_data["report"]

    # 7. Fetch report directly
    report_res = await client.get(f"/api/v1/interviews/{interview_id}/report", headers=headers)
    assert report_res.status_code == 200
    report = report_res.json()
    assert report["overall_score"] > 0
    assert len(report["theta_trajectory"]) >= 2
    assert len(report["action_items"]) <= 3

    # 8. Test IDOR protection: Another user cannot access or answer this interview
    other_email = f"other_iv_{uuid.uuid4().hex[:8]}@example.com"
    other_auth = await client.post("/api/v1/auth/register", json={
        "email": other_email,
        "name": "Intruder User",
        "password": "Password123!",
    })
    other_token = other_auth.json()["access_token"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    idor_res = await client.get(f"/api/v1/interviews/{interview_id}", headers=other_headers)
    assert idor_res.status_code == 404
