import uuid

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.core.ratelimit import check_and_increment_llm_quota, limiter
from app.models.models import ActivityEvent, ATSAnalysis, JobDescription, Resume, User
from app.schemas.ats import ATSAnalysisResponse, ATSAnalyzeRequest
from app.schemas.common import PaginatedResponse
from app.services.ats.extractor import get_taxonomy_matcher
from app.services.ats.parser import normalize_text
from app.services.ats.scorer import score_resume_against_jd

router = APIRouter(prefix="/ats", tags=["ats"])

@router.post("/analyze", response_model=ATSAnalysisResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def analyze_resume_ats(
    request: Request,
    payload: ATSAnalyzeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. Fetch resume (IDOR protected)
    stmt = select(Resume).where(and_(Resume.id == payload.resume_id, Resume.user_id == current_user.id))
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found")

    # 2. Fetch or create Job Description
    if payload.jd_id:
        jd_stmt = select(JobDescription).where(
            and_(JobDescription.id == payload.jd_id, JobDescription.user_id == current_user.id)
        )
        jd = (await db.execute(jd_stmt)).scalar_one_or_none()
        if not jd:
            raise NotFoundError("Job description not found")
    elif payload.inline_jd_text:
        clean_jd_text = normalize_text(payload.inline_jd_text)
        if len(clean_jd_text) < 20:
            raise ValidationError("Job description text must be at least 20 characters")
        matcher = get_taxonomy_matcher()
        weighted_skills = matcher.extract_weighted_skills_from_jd(clean_jd_text)
        jd = JobDescription(
            user_id=current_user.id,
            company=payload.company or "Target Company",
            role=payload.role or "Software Engineer",
            jd_text=clean_jd_text,
            extracted={"skills": weighted_skills},
        )
        db.add(jd)
        await db.flush()
    else:
        raise ValidationError("Either jd_id or inline_jd_text must be provided")

    # 3. Check & increment daily LLM quota
    await check_and_increment_llm_quota(current_user.id, db)

    # 4. Score resume against JD
    score_result = await score_resume_against_jd(
        resume_text=resume.content_text,
        parsed_resume=resume.parsed or {},
        jd_text=jd.jd_text,
        jd_role=jd.role,
    )

    # 5. Persist ATS analysis
    analysis = ATSAnalysis(
        user_id=current_user.id,
        resume_id=resume.id,
        jd_id=jd.id,
        overall=score_result["overall"],
        keyword_score=score_result["keyword_score"],
        semantic_score=score_result["semantic_score"],
        tfidf_score=score_result["tfidf_score"],
        quality_score=score_result["quality_score"],
        matched=score_result["matched"],
        missing=score_result["missing"],
        suggestions=score_result["suggestions"],
        degraded=score_result["degraded"],
    )
    db.add(analysis)
    await db.flush()

    # Log activity event
    event = ActivityEvent(
        user_id=current_user.id,
        type="ats_run",
        title=f"ATS Analysis: {resume.title} vs {jd.company} ({jd.role})",
        detail={
            "overall": analysis.overall,
            "keyword_score": analysis.keyword_score,
            "quality_score": analysis.quality_score,
        },
    )
    db.add(event)
    await db.commit()
    await db.refresh(analysis)

    return ATSAnalysisResponse.model_validate(analysis)

@router.get("/analyses", response_model=PaginatedResponse[ATSAnalysisResponse])
async def list_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ATSAnalysis)
        .options(selectinload(ATSAnalysis.resume), selectinload(ATSAnalysis.job_description))
        .where(ATSAnalysis.user_id == current_user.id)
        .order_by(ATSAnalysis.created_at.desc())
    )
    analyses = (await db.execute(stmt)).scalars().all()
    items = [ATSAnalysisResponse.model_validate(a) for a in analyses]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)

@router.get("/analyses/{analysis_id}", response_model=ATSAnalysisResponse)
async def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ATSAnalysis)
        .options(selectinload(ATSAnalysis.resume), selectinload(ATSAnalysis.job_description))
        .where(and_(ATSAnalysis.id == analysis_id, ATSAnalysis.user_id == current_user.id))
    )
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if not analysis:
        raise NotFoundError("ATS analysis not found")
    return ATSAnalysisResponse.model_validate(analysis)
