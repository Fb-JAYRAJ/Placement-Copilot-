import uuid

import pytest
from httpx import AsyncClient

FIXTURE_BACKEND_RESUME = """
Alex Developer
alex.developer@example.com | (555) 123-4567 | github.com/alexdev | linkedin.com/in/alexdev

EDUCATION
University of California, Berkeley - B.S. in Computer Science (2024)

TECHNICAL SKILLS
Languages: Python, Go, SQL, Bash
Frameworks: FastAPI, Flask, Django, Docker
Databases: PostgreSQL, Redis, MongoDB
Tools: Git, GitHub Actions, Linux, Postman

WORK EXPERIENCE
Backend Software Engineer Intern - TechFlow Systems (June 2023 - Present)
• Architected high-throughput microservices using Python and FastAPI, handling over 12,000 requests per minute with 99.9% uptime.
• Optimized PostgreSQL query execution plans and database indexing, reducing p99 latency by 45%.
• Deployed Redis caching cluster for session and rate limiting management, preventing database saturation during peak traffic.
• Engineered automated CI/CD deployment pipelines using GitHub Actions and Docker, reducing build delivery times from 25 minutes to 4 minutes.

PROJECTS
Distributed Key-Value Store
• Developed an in-memory distributed key-value storage engine in Go utilizing Raft consensus protocol.
• Implemented consistent hashing ring with virtual nodes, balancing partition workloads across 5 cluster nodes.
"""

FIXTURE_FRONTEND_RESUME = """
Taylor Designer
taylor.design@example.com | (555) 987-6543 | portfolio.dev

EDUCATION
Design & Art Institute - B.A. in Digital Arts (2023)

TECHNICAL SKILLS
Languages: HTML5, CSS3, JavaScript
Frameworks: React, Tailwind CSS, Vue.js, Figma
Tools: Git, npm, Webpack

WORK EXPERIENCE
Junior Frontend UI Developer - CreativePixels (2023 - Present)
• Created responsive web components using React and Tailwind CSS for client landing pages.
• Collaborated with design teams in Figma to translate mockups into semantic HTML5 and CSS3 layouts.
• Fixed cross-browser CSS styling inconsistencies across Safari, Chrome, and Firefox browsers.
"""

FIXTURE_BACKEND_JD = """
Company: Apex Cloud Infrastructure
Role: Senior Backend Engineer

About the Role:
We are seeking a Backend Engineer to build robust cloud infrastructure.

Required Qualifications:
• 2+ years of experience with Python and modern async frameworks such as FastAPI.
• Deep proficiency with relational databases, specifically PostgreSQL indexing and query optimization.
• Solid background with in-memory caching solutions like Redis.
• Experience containerizing microservices with Docker and deploying to AWS.

Preferred Qualifications:
• Familiarity with Kubernetes cluster management and Helm charts.
• Experience with Go or distributed systems consensus protocols.
• Knowledge of CI/CD pipeline automation with GitHub Actions.
"""

@pytest.mark.asyncio
async def test_ats_full_pipeline_and_fixtures(client: AsyncClient):
    # 1. Register candidate user
    email = f"ats_test_{uuid.uuid4().hex[:8]}@example.com"
    res_auth = await client.post("/api/v1/auth/register", json={
        "email": email,
        "name": "Alex Candidate",
        "password": "Password123!",
    })
    token = res_auth.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload Backend Resume (Text)
    res_resume = await client.post(
        "/api/v1/resumes",
        data={"title": "Backend Engineering Resume", "content_text": FIXTURE_BACKEND_RESUME},
        headers=headers,
    )
    assert res_resume.status_code == 201
    backend_resume_id = res_resume.json()["id"]

    # 3. Upload Frontend Resume (Text)
    res_front = await client.post(
        "/api/v1/resumes",
        data={"title": "Frontend Resume", "content_text": FIXTURE_FRONTEND_RESUME},
        headers=headers,
    )
    assert res_front.status_code == 201
    front_resume_id = res_front.json()["id"]

    # 4. Create Job Description
    res_jd = await client.post(
        "/api/v1/job-descriptions",
        json={
            "company": "Apex Cloud",
            "role": "Senior Backend Engineer",
            "jd_text": FIXTURE_BACKEND_JD,
        },
        headers=headers,
    )
    assert res_jd.status_code == 201
    jd_id = res_jd.json()["id"]

    # 5. Analyze Backend Resume against Backend JD
    analyze_res1 = await client.post(
        "/api/v1/ats/analyze",
        json={"resume_id": backend_resume_id, "jd_id": jd_id},
        headers=headers,
    )
    assert analyze_res1.status_code == 201
    analysis1 = analyze_res1.json()

    # Verify score stability and components
    assert 0 <= analysis1["overall"] <= 100
    assert 0 <= analysis1["keyword_score"] <= 100
    assert 0 <= analysis1["quality_score"] <= 100
    assert 0 <= analysis1["tfidf_score"] <= 100

    matched_names = [m["name"].lower() for m in analysis1["matched"]]
    missing_names = [m["name"].lower() for m in analysis1["missing"]]

    # Backend resume should match Python, FastAPI, PostgreSQL, Redis, Docker
    assert any("python" in m for m in matched_names)
    assert any("fastapi" in m for m in matched_names)
    assert any("postgresql" in m for m in matched_names)
    assert any("redis" in m for m in matched_names)

    # Missing skills should contain AWS or Kubernetes from JD
    assert any("aws" in m or "kubernetes" in m for m in missing_names)

    # Verify evidence exists in matched skills
    for m in analysis1["matched"]:
        assert "evidence" in m and len(m["evidence"]) > 0

    # 6. Analyze Frontend Resume against Backend JD
    analyze_res2 = await client.post(
        "/api/v1/ats/analyze",
        json={"resume_id": front_resume_id, "jd_id": jd_id},
        headers=headers,
    )
    assert analyze_res2.status_code == 201
    analysis2 = analyze_res2.json()

    # Backend resume must score significantly higher than Frontend resume for Backend JD
    assert analysis1["overall"] > analysis2["overall"]
    assert analysis1["keyword_score"] > analysis2["keyword_score"]

    # 7. Test IDOR protection: Another user cannot view analysis
    other_email = f"other_{uuid.uuid4().hex[:8]}@example.com"
    res_other = await client.post("/api/v1/auth/register", json={
        "email": other_email,
        "name": "Other User",
        "password": "Password123!",
    })
    token_other = res_other.json()["access_token"]
    headers_other = {"Authorization": f"Bearer {token_other}"}

    idor_res = await client.get(f"/api/v1/ats/analyses/{analysis1['id']}", headers=headers_other)
    assert idor_res.status_code == 404
