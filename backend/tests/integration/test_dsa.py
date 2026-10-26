import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select

from app.models.models import DSAProblem, DSATopic, QuestionBank
from scripts.seed import run_seed


@pytest.mark.asyncio
async def test_seed_idempotency(db_session):
    """Running seed script twice must not duplicate topics, problems, or questions."""
    # Run seed once
    await run_seed(session=db_session)

    count_topics_before = (await db_session.execute(select(func.count(DSATopic.id)))).scalar()
    count_probs_before = (await db_session.execute(select(func.count(DSAProblem.id)))).scalar()
    count_qb_before = (await db_session.execute(select(func.count(QuestionBank.id)))).scalar()

    # Re-run seed to test idempotency
    await run_seed(session=db_session)

    count_topics_after = (await db_session.execute(select(func.count(DSATopic.id)))).scalar()
    count_probs_after = (await db_session.execute(select(func.count(DSAProblem.id)))).scalar()
    count_qb_after = (await db_session.execute(select(func.count(QuestionBank.id)))).scalar()

    assert count_topics_after == count_topics_before
    assert count_probs_after == count_probs_before
    assert count_qb_after == count_qb_before

@pytest.mark.asyncio
async def test_dsa_endpoints_and_idor(client: AsyncClient, db_session):
    # 1. Register User A
    user_a_email = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    res_a = await client.post("/api/v1/auth/register", json={
        "email": user_a_email,
        "name": "User A",
        "password": "Password123!",
    })
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B
    user_b_email = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    res_b = await client.post("/api/v1/auth/register", json={
        "email": user_b_email,
        "name": "User B",
        "password": "Password123!",
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. GET /dsa/topics
    topics_res = await client.get("/api/v1/dsa/topics")
    assert topics_res.status_code == 200
    t_data = topics_res.json()
    assert "items" in t_data and "total" in t_data
    topics = t_data["items"]
    assert len(topics) >= 20
    first_topic = topics[0]

    # 4. GET /dsa/problems with filters
    probs_res = await client.get("/api/v1/dsa/problems?difficulty=medium&limit=5")
    assert probs_res.status_code == 200
    p_data = probs_res.json()
    assert len(p_data["items"]) <= 5
    assert all(p["difficulty"] == "medium" for p in p_data["items"])

    # 5. User A logs an attempt
    attempt_payload = {
        "problem_id": p_data["items"][0]["id"],
        "topic_id": first_topic["id"],
        "difficulty": "medium",
        "status": "solved",
        "confidence": 4,
        "time_spent_min": 25,
        "notes": "Solved using hash map two pass",
    }
    att_res = await client.post("/api/v1/dsa/attempts", json=attempt_payload, headers=headers_a)
    assert att_res.status_code == 201
    attempt_data = att_res.json()
    attempt_id = attempt_data["id"]
    assert attempt_data["status"] == "solved"
    assert attempt_data["confidence"] == 4
    assert attempt_data["sm2_interval_days"] >= 1

    # User A gets attempts list (eager loading regression test)
    get_att_res = await client.get("/api/v1/dsa/attempts", headers=headers_a)
    assert get_att_res.status_code == 200
    att_list = get_att_res.json()["items"]
    assert len(att_list) >= 1
    assert att_list[0]["topic_name"] == first_topic["name"]
    assert att_list[0]["problem_title"] == p_data["items"][0]["title"]

    # 6. IDOR Check: User B tries to PATCH User A's attempt -> must fail with 404
    patch_payload = {"notes": "Hacked notes"}
    idor_patch = await client.patch(f"/api/v1/dsa/attempts/{attempt_id}", json=patch_payload, headers=headers_b)
    assert idor_patch.status_code == 404

    # 7. IDOR Check: User B tries to DELETE User A's attempt -> must fail with 404
    idor_del = await client.delete(f"/api/v1/dsa/attempts/{attempt_id}", headers=headers_b)
    assert idor_del.status_code == 404

    # 8. User A checks their mastery
    mastery_res = await client.get("/api/v1/dsa/mastery", headers=headers_a)
    assert mastery_res.status_code == 200
    m_data = mastery_res.json()
    assert "items" in m_data and "total" in m_data
    masteries = m_data["items"]
    matched_m = next((m for m in masteries if m["topic_id"] == first_topic["id"]), None)
    assert matched_m is not None
    assert matched_m["mastery"] > 0.0

    # 9. User A checks recommendations
    recs_res = await client.get("/api/v1/dsa/recommendations", headers=headers_a)
    assert recs_res.status_code == 200
    r_data = recs_res.json()
    assert "items" in r_data and "total" in r_data
    recs = r_data["items"]
    assert len(recs) == 5
    assert all("reason" in r and "title" in r for r in recs)

    # 10. User A checks stats
    stats_res = await client.get("/api/v1/dsa/stats", headers=headers_a)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_solved"] >= 1
    assert stats["topics_covered"] >= 1
    assert len(stats["solved_7d"]) == 7
