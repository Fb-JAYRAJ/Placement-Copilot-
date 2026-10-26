import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    ATSAnalysis,
    DSAAttempt,
    DSAAttemptStatus,
)
from app.services.dsa.recommendations import get_dsa_recommendations


async def determine_daily_focus_task(user_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
    now = datetime.now(UTC)

    # 1. Spaced Repetition review due
    due_stmt = (
        select(DSAAttempt)
        .options(selectinload(DSAAttempt.problem))
        .where(
            and_(
                DSAAttempt.user_id == user_id,
                DSAAttempt.status == DSAAttemptStatus.SOLVED,
                DSAAttempt.next_review_at.isnot(None),
                DSAAttempt.next_review_at <= now,
            )
        )
        .limit(1)
    )
    due_attempt = (await db.execute(due_stmt)).scalar_one_or_none()
    if due_attempt:
        title = due_attempt.problem.title if due_attempt.problem else (due_attempt.custom_title or "Spaced Review")
        return {
            "type": "dsa_review",
            "title": f"Review Due: {title}",
            "description": "Solidify your recall with your scheduled SM-2 spaced repetition review.",
            "cta_label": "Start Review",
            "cta_url": "/dsa",
            "priority": 1,
        }

    # 2. Recommended problem for weakest topic
    recs = await get_dsa_recommendations(user_id, db, limit=1)
    if recs:
        rec = recs[0]
        return {
            "type": "dsa_solve",
            "title": f"Practice: {rec['title']} ({rec['topic_name']})",
            "description": rec["reason"],
            "cta_label": "Solve Problem",
            "cta_url": f"/dsa?problem={rec['slug']}",
            "priority": 2,
        }

    # 3. Analyze your resume if no recent analysis
    ats_stmt = select(ATSAnalysis).where(ATSAnalysis.user_id == user_id).limit(1)
    ats_run = (await db.execute(ats_stmt)).scalar_one_or_none()
    if not ats_run:
        return {
            "type": "resume_analyze",
            "title": "Analyze Your Resume for ATS Alignment",
            "description": "Target your resume against real job descriptions to identify missing skills and optimize bullet points.",
            "cta_label": "Analyze Resume",
            "cta_url": "/resume",
            "priority": 3,
        }

    # 4. Take a mock interview
    return {
        "type": "mock_interview",
        "title": "Practice with Adaptive Mock Interview",
        "description": "Benchmark your problem-solving depth and test your technical responses under pressure.",
        "cta_label": "Start Mock Interview",
        "cta_url": "/interview",
        "priority": 4,
    }
