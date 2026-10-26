import asyncio
import os
import sys
from datetime import datetime, date, timedelta, timezone
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select, delete

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.models import (
    User,
    Resume,
    JobDescription,
    ATSAnalysis,
    DSATopic,
    DSAProblem,
    DSAAttempt,
    DSAAttemptStatus,
    MockInterview,
    InterviewQuestion,
    InterviewAnswer,
    MockInterviewStatus,
    QuestionSource,
    InterviewTrack,
    ReadinessSnapshot,
    ActivityEvent,
)
from app.services.dsa.mastery import recompute_and_save_topic_mastery
from app.services.ats.parser import parse_sections_and_contact, normalize_text
from app.services.ats.scorer import score_resume_against_jd
from app.services.readiness.calculator import (
    calculate_ats_component,
    calculate_dsa_component,
    calculate_interview_component,
    calculate_consistency_component,
    calculate_composite_readiness,
    simulate_levers,
)

DEMO_RESUME = """
Jayraj Sawant
jayraj.sawant@example.com | +91 98765 43210 | github.com/jayrajsawant | linkedin.com/in/jayrajsawant

EDUCATION
Indian Institute of Technology - B.Tech in Computer Science and Engineering (Graduation: 2026)
GPA: 9.2 / 10.0

TECHNICAL SKILLS
Languages: Python, Go, TypeScript, C++, SQL, Bash
Backend & Systems: FastAPI, PostgreSQL, Redis, Docker, Kubernetes, gRPC, RabbitMQ
System Design: Distributed Systems, Microservices, Event-Driven Architecture, Caching
Tools: Git, GitHub Actions, Linux, Terraform, Prometheus, Grafana

WORK EXPERIENCE
Systems Engineering Intern - CloudScale Technologies (May 2025 - August 2025)
• Architected and deployed an asynchronous task orchestration engine using Python, FastAPI, and Redis Pub/Sub, processing over 150,000 tasks daily with sub-50ms queue dispatch latency.
• Optimized PostgreSQL query execution plans, indexes, and connection pooling with PgBouncer, achieving a 42% reduction in p99 database response times.
• Engineered distributed tracing instrumentation using OpenTelemetry and Prometheus, reducing mean time to detect (MTTD) operational anomalies from 45 minutes to under 3 minutes.
• Streamlined CI/CD build workflows via Docker and GitHub Actions, cutting release deployment cycles from 28 minutes to 4 minutes.

PROJECTS
Placement Copilot - AI Technical Mastery Platform
• Engineered full-stack placement prep platform with React 19, FastAPI, and Neon Postgres, integrating Item Response Theory (IRT) adaptive interviews and deterministic ATS scoring.
• Implemented SM-2 spaced repetition engine and 45-day exponential decay mastery algorithm over 140+ DSA problems.
• Automated bullet point rewrite coaching using Google Gemini with structured Pydantic schema validation.

Distributed Consensus Key-Value Store
• Implemented a fault-tolerant distributed key-value storage system in Go based on the Raft consensus protocol.
• Supported dynamic cluster membership changes, log compaction with snapshotting, and linearizable read operations under network partitions.
"""

DEMO_JD = """
Company: Google
Role: Software Engineer, Systems & Infrastructure

About the Role:
Google infrastructure teams develop next-generation technologies that change how billions of users connect, explore, and interact with information. We are looking for engineers with a strong foundation in core computer science, distributed systems, and scalable backend services.

Required Qualifications:
• Bachelor's degree in Computer Science, Computer Engineering, or equivalent practical experience.
• Experience with programming in one or more languages: Python, Go, C++, or Java.
• Strong foundation in Data Structures, Algorithms, and Software Design.
• Experience designing and optimizing relational databases (e.g. PostgreSQL, Spanner) and in-memory caches (Redis).
• Knowledge of containerization with Docker and cloud microservices.

Preferred Qualifications:
• Experience with Distributed Systems, Consensus Algorithms (Raft, Paxos), or RPC frameworks (gRPC).
• Experience with CI/CD automation, Kubernetes cluster orchestration, and observability tools (Prometheus, Grafana).
"""

async def seed_demo():
    print("=== Seeding Labelled Demo Account: scripts/seed_demo.py ===")
    engine = create_async_engine(settings.DATABASE_URL, connect_args={"prepare_threshold": None})
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Check or create demo user
        demo_email = "demo@placementcopilot.com"
        stmt = select(User).where(User.email == demo_email)
        user = (await db.execute(stmt)).scalar_one_or_none()

        if user:
            print(f"Resetting existing demo account: {demo_email}")
            await db.delete(user)
            await db.commit()

        user = User(
            email=demo_email,
            name="Jayraj Sawant",
            password_hash=get_password_hash("DemoCandidate2026!"),
            college="Indian Institute of Technology",
            grad_year=2026,
            target_role="Senior Backend Engineer",
            target_companies=["Google", "Stripe", "Uber", "Databricks"],
        )
        db.add(user)
        await db.flush()
        print(f"✓ Created Demo User: {user.name} ({user.email})")

        # 1. Resume
        norm_resume = normalize_text(DEMO_RESUME)
        parsed_resume = parse_sections_and_contact(norm_resume)
        resume = Resume(
            user_id=user.id,
            title="Jayraj Sawant - Systems Resume",
            filename="jayraj_sawant_resume.pdf",
            file_type="pdf",
            content_text=norm_resume,
            parsed=parsed_resume,
            is_primary=True,
        )
        db.add(resume)
        await db.flush()

        # 2. Job Description
        norm_jd = normalize_text(DEMO_JD)
        jd = JobDescription(
            user_id=user.id,
            company="Google",
            role="Software Engineer, Systems & Infrastructure",
            jd_text=norm_jd,
        )
        db.add(jd)
        await db.flush()

        # 3. Real ATS Analysis
        score_res = await score_resume_against_jd(
            resume_text=norm_resume,
            parsed_resume=parsed_resume,
            jd_text=norm_jd,
            jd_role=jd.role,
        )
        ats_analysis = ATSAnalysis(
            user_id=user.id,
            resume_id=resume.id,
            jd_id=jd.id,
            overall=score_res["overall"],
            keyword_score=score_res["keyword_score"],
            semantic_score=score_res["semantic_score"],
            tfidf_score=score_res["tfidf_score"],
            quality_score=score_res["quality_score"],
            matched=score_res["matched"],
            missing=score_res["missing"],
            suggestions=score_res["suggestions"],
            degraded=score_res["degraded"],
        )
        db.add(ats_analysis)
        await db.flush()
        print(f"✓ Generated ATS Analysis: Overall Score {ats_analysis.overall}%")

        # 4. DSA Attempts & Mastery
        now = datetime.now(timezone.utc)
        topics = (await db.execute(select(DSATopic))).scalars().all()
        topic_by_slug = {t.slug: t for t in topics}

        problems = (await db.execute(select(DSAProblem))).scalars().all()
        prob_by_slug = {p.slug: p for p in problems}

        demo_attempts_plan = [
            ("arrays-and-hashing", "two-sum", "easy", 5, 12, 10),
            ("arrays-and-hashing", "group-anagrams", "medium", 4, 25, 9),
            ("arrays-and-hashing", "product-of-array-except-self", "medium", 5, 20, 8),
            ("two-pointers", "3sum", "medium", 4, 35, 7),
            ("two-pointers", "container-with-most-water", "medium", 5, 18, 6),
            ("sliding-window", "longest-substring-without-repeating-characters", "medium", 5, 22, 5),
            ("sliding-window", "minimum-window-substring", "hard", 4, 45, 4),
            ("binary-search", "search-in-rotated-sorted-array", "medium", 4, 28, 3),
            ("trees", "lowest-common-ancestor-of-a-binary-search-tree", "medium", 5, 15, 2),
            ("trees", "binary-tree-level-order-traversal", "medium", 5, 14, 2),
            ("graphs", "number-of-islands", "medium", 5, 20, 1),
            ("graphs", "course-schedule", "medium", 4, 30, 1),
            ("1d-dynamic-programming", "coin-change", "medium", 4, 32, 0),
            ("1d-dynamic-programming", "longest-increasing-subsequence", "medium", 4, 35, 0),
        ]

        for topic_slug, prob_slug, diff, conf, time_spent, days_ago in demo_attempts_plan:
            top = topic_by_slug.get(topic_slug)
            prob = prob_by_slug.get(prob_slug)
            if not top or not prob:
                continue
            
            att_time = now - timedelta(days=days_ago, hours=2)
            attempt = DSAAttempt(
                user_id=user.id,
                problem_id=prob.id,
                custom_title=None,
                topic_id=top.id,
                difficulty=diff,
                status=DSAAttemptStatus.SOLVED,
                confidence=conf,
                time_spent_min=time_spent,
                notes=f"Solved optimally using canonical patterns. Clean O(1) space where applicable.",
                attempted_at=att_time,
                solved_at=att_time,
                sm2_ease=2.6,
                sm2_interval_days=max(1, days_ago * 2),
                sm2_repetitions=2,
                next_review_at=now + timedelta(days=max(1, 10 - days_ago)),
            )
            db.add(attempt)
            await db.flush()
            await recompute_and_save_topic_mastery(user.id, top.id, db)

        print("✓ Logged 14 DSA attempts across 6 topics with recomputed mastery.")

        # 5. Mock Interviews
        iv1_start = now - timedelta(days=5)
        iv1 = MockInterview(
            user_id=user.id,
            track=InterviewTrack.DSA_CONCEPTS,
            company="Google",
            role="Systems Software Engineer",
            planned_questions=3,
            status=MockInterviewStatus.COMPLETED,
            ability=3.8,
            final_score=8.4,
            report={
                "overall_score": 8.4,
                "final_ability": 3.8,
                "theta_trajectory": [2.5, 3.1, 3.5, 3.8],
                "per_topic_scores": {
                    "Binary Search Invariants": {"average_score": 8.8, "questions_count": 1},
                    "Graph Traversals": {"average_score": 8.2, "questions_count": 1},
                    "Dynamic Programming": {"average_score": 8.2, "questions_count": 1},
                },
                "top_gaps": ["Detail memory layout and CPU cache locality benefits."],
                "action_items": [
                    "Review core fundamentals addressing: CPU cache locality",
                    "Practice 2-3 medium problems in '2-D Dynamic Programming'",
                ],
                "delta_vs_previous": None,
            },
            started_at=iv1_start,
            ended_at=iv1_start + timedelta(minutes=35),
        )
        db.add(iv1)
        await db.flush()

        # Add questions and answers for iv1
        q_texts = [
            ("Binary Search Invariants", 2.5, "How do you avoid integer overflow and off-by-one errors when implementing binary search?"),
            ("Graph Traversals", 3.2, "Explain why BFS guarantees shortest paths on unweighted graphs while DFS does not."),
            ("Dynamic Programming", 3.6, "Explain state transition difference between 0/1 Knapsack and Unbounded Knapsack."),
        ]
        for idx, (top_name, b_val, txt) in enumerate(q_texts, start=1):
            q_rec = InterviewQuestion(
                interview_id=iv1.id,
                seq=idx,
                topic=top_name,
                difficulty=b_val,
                text=txt,
                ideal_points=["Correct asymptotic complexity", "Boundary invariants", "Trade-offs"],
                source=QuestionSource.BANK,
            )
            db.add(q_rec)
            await db.flush()
            ans_rec = InterviewAnswer(
                question_id=q_rec.id,
                answer_text="Demonstrated thorough technical precision covering boundary invariants and optimal complexity bounds.",
                scores={"correctness": 8.5, "depth": 8.2, "structure": 8.5, "communication": 8.8},
                overall=8.4,
                feedback={"strengths": ["Clear communication", "Optimal code complexity"], "gaps": ["Could elaborate on CPU cache"]},
                time_taken_sec=45,
                degraded=False,
            )
            db.add(ans_rec)

        print("✓ Created completed DSA Mock Interview session with trajectory [2.5 -> 3.8]")

        # 6. Readiness Snapshots (Historical 7 days ago and current)
        snap_past = ReadinessSnapshot(
            user_id=user.id,
            ats=78.0,
            dsa=72.0,
            interview=80.0,
            consistency=75.0,
            composite=76.8,
            confidence=1.0,
            explanation={"notes": "Historical baseline 7 days ago"},
            created_at=now - timedelta(days=8),
        )
        db.add(snap_past)

        # Current snapshot
        snap_curr = ReadinessSnapshot(
            user_id=user.id,
            ats=score_res["overall"],
            dsa=78.5,
            interview=84.0,
            consistency=88.0,
            composite=82.4,
            confidence=1.0,
            explanation={"notes": "Latest readiness score"},
            created_at=now - timedelta(hours=1),
        )
        db.add(snap_curr)

        # 7. Activity Events
        events = [
            ("ats_run", "Analyzed Resume vs Google (Software Engineer)", {"overall": score_res["overall"]}),
            ("dsa_attempt", "Solved Longest Increasing Subsequence (Medium)", {"status": "solved"}),
            ("dsa_attempt", "Solved Course Schedule (Medium)", {"status": "solved"}),
            ("mock_interview_completed", "Completed DSA Concepts Mock Interview (Score: 8.4)", {"score": 8.4}),
            ("account_created", "Created Placement Copilot Account", {}),
        ]
        for ev_type, ev_title, ev_detail in events:
            ev = ActivityEvent(
                user_id=user.id,
                type=ev_type,
                title=ev_title,
                detail=ev_detail,
                created_at=now - timedelta(hours=2),
            )
            db.add(ev)

        await db.commit()
        print("✓ Activity feed and historical readiness snapshots successfully seeded!")
        print("=== Demo Account Seeding Complete! ===")
        print(f"Login Credentials: {demo_email} / DemoCandidate2026!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_demo())
