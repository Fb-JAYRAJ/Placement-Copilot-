import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.models import DSAAttempt, DSAProblem, DSATopic
from scripts.seed import run_seed


@pytest.mark.asyncio
async def test_relationship_eager_loading_regression(client: AsyncClient, db_session):
    """
    Regression test suite ensuring async SQLAlchemy eagerly loads all relationships
    across list and detail endpoints without MissingGreenlet exceptions:
    1. DSA attempts list (GET /api/v1/dsa/attempts) reading a.topic.name and a.problem.title
    2. DSA reviews due (GET /api/v1/dsa/reviews/due) and dashboard daily focus task with due review
    3. Mock interview detail (GET /api/v1/interviews/{id}) and list (GET /api/v1/interviews)
    4. Mock interview report (GET /api/v1/interviews/{id}/report)
    5. ATS analyses list (GET /api/v1/ats/analyses) and detail (GET /api/v1/ats/analyses/{id})
    6. Candidate data export (GET /api/v1/users/me/export) reading cross-table relationships
    """
    # 0. Ensure seed catalog (topics, problems, question bank) exists in test DB
    await run_seed(session=db_session)

    topic = (await db_session.execute(select(DSATopic))).scalars().first()
    assert topic is not None, "DSATopic must exist after seeding"
    problem = (await db_session.execute(select(DSAProblem))).scalars().first()
    assert problem is not None, "DSAProblem must exist after seeding"

    # 1. Register candidate
    email = f"regression_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "name": "Regression Tester",
            "password": "Password123!",
            "college": "Test University",
            "grad_year": 2026,
            "target_role": "Backend Engineer",
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. DSA Attempt creation and attempts list regression
    create_att_res = await client.post(
        "/api/v1/dsa/attempts",
        json={
            "problem_id": str(problem.id),
            "topic_id": str(topic.id),
            "difficulty": "medium",
            "status": "solved",
            "confidence": 5,
            "time_spent_min": 20,
            "notes": "Optimal solution test",
        },
        headers=headers,
    )
    assert create_att_res.status_code == 201, create_att_res.text
    attempt_id = create_att_res.json()["id"]

    # Call GET /api/v1/dsa/attempts (Regression: previously failed with 500 MissingGreenlet at line 222)
    list_att_res = await client.get("/api/v1/dsa/attempts", headers=headers)
    assert list_att_res.status_code == 200, f"Expected 200, got {list_att_res.status_code}: {list_att_res.text}"
    att_items = list_att_res.json()["items"]
    assert len(att_items) >= 1
    matched_att = next((a for a in att_items if a["id"] == attempt_id), None)
    assert matched_att is not None
    assert matched_att["topic_name"] == topic.name
    assert matched_att["problem_title"] == problem.title

    # Call PATCH /api/v1/dsa/attempts/{id} to verify update eager-loading
    patch_att_res = await client.patch(
        f"/api/v1/dsa/attempts/{attempt_id}",
        json={"notes": "Updated regression notes", "confidence": 4},
        headers=headers,
    )
    assert patch_att_res.status_code == 200, patch_att_res.text
    assert patch_att_res.json()["topic_name"] == topic.name
    assert patch_att_res.json()["problem_title"] == problem.title

    # 3. Trigger due review to verify reviews/due and dashboard focus_task eager-loading
    db_attempt = (
        await db_session.execute(select(DSAAttempt).where(DSAAttempt.id == uuid.UUID(attempt_id)))
    ).scalar_one()
    db_attempt.next_review_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    reviews_due_res = await client.get("/api/v1/dsa/reviews/due", headers=headers)
    assert reviews_due_res.status_code == 200, reviews_due_res.text
    r_data = reviews_due_res.json()
    assert "items" in r_data and "total" in r_data
    reviews = r_data["items"]
    assert len(reviews) >= 1
    assert reviews[0]["title"] == problem.title
    assert reviews[0]["topic_name"] == topic.name

    # Check dashboard summary with due review
    dash_res = await client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash_res.status_code == 200, dash_res.text
    dash_data = dash_res.json()
    assert dash_data["daily_focus_task"]["type"] == "dsa_review"
    assert problem.title in dash_data["daily_focus_task"]["title"]

    # 4. Resume & ATS Analysis regression
    resume_text = (
        "Alice Engineer\nalice@example.com | (555) 000-1111\n\n"
        "EDUCATION\nTech College - B.S. in Computer Science\n\n"
        "EXPERIENCE\nBackend Intern at TechCorp\n"
        "• Designed and engineered scalable REST APIs in Python using FastAPI and PostgreSQL database indexing.\n"
        "• Implemented Redis caching layers reducing latency by 40% across microservices.\n"
        "• Automated container deployments with Docker and GitHub Actions.\n\n"
        "SKILLS\nPython, FastAPI, PostgreSQL, Redis, Docker, Git"
    )
    resume_res = await client.post(
        "/api/v1/resumes",
        data={"title": "Regression Resume", "content_text": resume_text},
        headers=headers,
    )
    assert resume_res.status_code == 201, resume_res.text
    resume_id = resume_res.json()["id"]

    jd_text = (
        "Role: Senior Backend Engineer\nCompany: Stripe\n\n"
        "Requirements:\n"
        "• Proficient in Python, FastAPI, and PostgreSQL database optimization.\n"
        "• Hands-on experience with Redis caching and Docker containerization.\n"
    )
    jd_res = await client.post(
        "/api/v1/job-descriptions",
        json={"company": "Stripe", "role": "Senior Backend Engineer", "jd_text": jd_text},
        headers=headers,
    )
    assert jd_res.status_code == 201, jd_res.text
    jd_id = jd_res.json()["id"]

    analyze_res = await client.post(
        "/api/v1/ats/analyze",
        json={"resume_id": resume_id, "jd_id": jd_id},
        headers=headers,
    )
    assert analyze_res.status_code == 201, analyze_res.text
    analysis_id = analyze_res.json()["id"]

    # Call GET /api/v1/ats/analyses (list)
    list_ats_res = await client.get("/api/v1/ats/analyses", headers=headers)
    assert list_ats_res.status_code == 200, list_ats_res.text
    ats_data = list_ats_res.json()
    assert "items" in ats_data and "total" in ats_data
    analyses = ats_data["items"]
    assert len(analyses) >= 1
    assert any(a["id"] == analysis_id for a in analyses)

    # Call GET /api/v1/ats/analyses/{analysis_id} (detail)
    detail_ats_res = await client.get(f"/api/v1/ats/analyses/{analysis_id}", headers=headers)
    assert detail_ats_res.status_code == 200, detail_ats_res.text
    assert detail_ats_res.json()["id"] == analysis_id

    # 5. Mock Interview detail and report regression
    create_iv_res = await client.post(
        "/api/v1/interviews",
        json={
            "track": "dsa_concepts",
            "company": "Google",
            "role": "Software Engineer",
            "planned_questions": 3,
        },
        headers=headers,
    )
    assert create_iv_res.status_code == 201, create_iv_res.text
    interview_id = create_iv_res.json()["id"]
    q1 = create_iv_res.json()["current_question"]

    # Answer question 1
    ans_res = await client.post(
        f"/api/v1/interviews/{interview_id}/answers",
        json={
            "question_id": q1["id"],
            "answer_text": "Binary search maintains invariant left <= right, computing mid = left + (right - left) // 2.",
            "time_taken_sec": 30,
        },
        headers=headers,
    )
    assert ans_res.status_code == 200, ans_res.text

    # Call GET /api/v1/interviews (list)
    list_iv_res = await client.get("/api/v1/interviews", headers=headers)
    assert list_iv_res.status_code == 200, list_iv_res.text
    iv_data = list_iv_res.json()
    assert "items" in iv_data and "total" in iv_data
    iv_items = iv_data["items"]
    assert len(iv_items) >= 1
    matched_iv = next((i for i in iv_items if i["id"] == interview_id), None)
    assert matched_iv is not None
    assert matched_iv["questions_answered_count"] == 1

    # Call GET /api/v1/interviews/{interview_id} (detail)
    detail_iv_res = await client.get(f"/api/v1/interviews/{interview_id}", headers=headers)
    assert detail_iv_res.status_code == 200, detail_iv_res.text
    assert detail_iv_res.json()["questions_answered_count"] == 1
    assert detail_iv_res.json()["current_question"] is not None

    # Call finish and GET /api/v1/interviews/{interview_id}/report
    finish_res = await client.post(f"/api/v1/interviews/{interview_id}/finish", headers=headers)
    assert finish_res.status_code == 200, finish_res.text

    report_res = await client.get(f"/api/v1/interviews/{interview_id}/report", headers=headers)
    assert report_res.status_code == 200, report_res.text
    rep = report_res.json()
    assert "overall_score" in rep
    assert "theta_trajectory" in rep
    assert "action_items" in rep

    # 6. Candidate Data Export regression (GET /api/v1/users/me/export)
    export_res = await client.get("/api/v1/users/me/export", headers=headers)
    assert export_res.status_code == 200, f"Expected 200, got {export_res.status_code}: {export_res.text}"
    exp = export_res.json()
    assert "user" in exp
    assert exp["user"]["email"] == email
    assert len(exp["resumes"]) >= 1
    assert len(exp["job_descriptions"]) >= 1
    assert len(exp["ats_analyses"]) >= 1
    assert exp["ats_analyses"][0]["resume_title"] is not None
    assert exp["ats_analyses"][0]["job_company"] is not None
    assert len(exp["dsa_attempts"]) >= 1
    assert exp["dsa_attempts"][0]["topic_name"] == topic.name
    assert exp["dsa_attempts"][0]["problem_title"] == problem.title
    assert len(exp["mock_interviews"]) >= 1
    assert len(exp["mock_interviews"][0]["questions"]) >= 1
    assert exp["mock_interviews"][0]["questions"][0]["answer"] is not None
