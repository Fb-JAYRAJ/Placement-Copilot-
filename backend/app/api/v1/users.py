from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import UnauthorizedError
from app.core.security import get_password_hash, validate_password_strength, verify_password
from app.models.models import (
    ActivityEvent,
    ATSAnalysis,
    DSAAttempt,
    InterviewQuestion,
    JobDescription,
    MockInterview,
    ReadinessSnapshot,
    Resume,
    User,
)
from app.schemas.auth import ChangePasswordRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)

@router.patch("/me", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.name is not None:
        current_user.name = payload.name
    if payload.college is not None:
        current_user.college = payload.college
    if payload.grad_year is not None:
        current_user.grad_year = payload.grad_year
    if payload.target_role is not None:
        current_user.target_role = payload.target_role
    if payload.target_companies is not None:
        current_user.target_companies = payload.target_companies

    current_user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)

@router.post("/me/password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise UnauthorizedError("Current password is incorrect")
    
    validate_password_strength(payload.new_password)
    current_user.password_hash = get_password_hash(payload.new_password)
    current_user.updated_at = datetime.now(UTC)
    await db.commit()
    return {"message": "Password updated successfully"}

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Hard delete - CASCADE will delete all related records
    await db.delete(current_user)
    await db.commit()

@router.get("/me/export")
async def export_my_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    # Collect all user data across all tables with eager loaded relationships
    resumes = (await db.execute(select(Resume).where(Resume.user_id == current_user.id))).scalars().all()
    jds = (await db.execute(select(JobDescription).where(JobDescription.user_id == current_user.id))).scalars().all()
    ats = (
        await db.execute(
            select(ATSAnalysis)
            .options(selectinload(ATSAnalysis.resume), selectinload(ATSAnalysis.job_description))
            .where(ATSAnalysis.user_id == current_user.id)
        )
    ).scalars().all()
    attempts = (
        await db.execute(
            select(DSAAttempt)
            .options(selectinload(DSAAttempt.topic), selectinload(DSAAttempt.problem))
            .where(DSAAttempt.user_id == current_user.id)
        )
    ).scalars().all()
    interviews = (
        await db.execute(
            select(MockInterview)
            .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
            .where(MockInterview.user_id == current_user.id)
        )
    ).scalars().all()
    snapshots = (await db.execute(select(ReadinessSnapshot).where(ReadinessSnapshot.user_id == current_user.id))).scalars().all()
    events = (await db.execute(select(ActivityEvent).where(ActivityEvent.user_id == current_user.id))).scalars().all()

    return {
        "user": UserResponse.model_validate(current_user).model_dump(),
        "resumes": [
            {
                "id": str(r.id),
                "title": r.title,
                "file_type": r.file_type,
                "created_at": r.created_at.isoformat(),
                "parsed": r.parsed,
            }
            for r in resumes
        ],
        "job_descriptions": [
            {
                "id": str(j.id),
                "company": j.company,
                "role": j.role,
                "extracted": j.extracted,
                "created_at": j.created_at.isoformat(),
            }
            for j in jds
        ],
        "ats_analyses": [
            {
                "id": str(a.id),
                "resume_id": str(a.resume_id),
                "resume_title": a.resume.title if a.resume else None,
                "jd_id": str(a.jd_id),
                "job_company": a.job_description.company if a.job_description else None,
                "job_role": a.job_description.role if a.job_description else None,
                "overall": a.overall,
                "scores": {
                    "keyword": a.keyword_score,
                    "semantic": a.semantic_score,
                    "tfidf": a.tfidf_score,
                    "quality": a.quality_score,
                },
                "matched": a.matched,
                "missing": a.missing,
                "suggestions": a.suggestions,
                "created_at": a.created_at.isoformat(),
            }
            for a in ats
        ],
        "dsa_attempts": [
            {
                "id": str(att.id),
                "problem_id": str(att.problem_id) if att.problem_id else None,
                "problem_title": att.problem.title if att.problem else None,
                "topic_id": str(att.topic_id),
                "topic_name": att.topic.name if att.topic else None,
                "custom_title": att.custom_title,
                "difficulty": att.difficulty,
                "status": att.status.value,
                "confidence": att.confidence,
                "attempted_at": att.attempted_at.isoformat(),
            }
            for att in attempts
        ],
        "mock_interviews": [
            {
                "id": str(i.id),
                "track": i.track.value,
                "status": i.status.value,
                "final_score": i.final_score,
                "report": i.report,
                "started_at": i.started_at.isoformat(),
                "questions": [
                    {
                        "id": str(q.id),
                        "seq": q.seq,
                        "topic": q.topic,
                        "difficulty": q.difficulty,
                        "text": q.text,
                        "answer": q.answer.answer_text if q.answer else None,
                    }
                    for q in i.questions
                ],
            }
            for i in interviews
        ],
        "readiness_snapshots": [
            {
                "id": str(s.id),
                "composite": s.composite,
                "confidence": s.confidence,
                "components": {"ats": s.ats, "dsa": s.dsa, "interview": s.interview, "consistency": s.consistency},
                "created_at": s.created_at.isoformat(),
            }
            for s in snapshots
        ],
        "activity_events": [
            {
                "id": str(e.id),
                "type": e.type,
                "title": e.title,
                "detail": e.detail,
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
    }
