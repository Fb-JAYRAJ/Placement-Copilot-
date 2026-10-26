import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models.models import JobDescription, User
from app.schemas.ats import JobDescriptionCreateRequest, JobDescriptionResponse
from app.schemas.common import PaginatedResponse
from app.services.ats.extractor import get_taxonomy_matcher
from app.services.ats.parser import normalize_text

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])

@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    payload: JobDescriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matcher = get_taxonomy_matcher()
    clean_text = normalize_text(payload.jd_text)
    weighted_skills = matcher.extract_weighted_skills_from_jd(clean_text)

    jd = JobDescription(
        user_id=current_user.id,
        company=payload.company.strip(),
        role=payload.role.strip(),
        jd_text=clean_text,
        extracted={"skills": weighted_skills},
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)

    return JobDescriptionResponse.model_validate(jd)

@router.get("", response_model=PaginatedResponse[JobDescriptionResponse])
async def list_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(JobDescription)
        .options(selectinload(JobDescription.ats_analyses))
        .where(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.created_at.desc())
    )
    jds = (await db.execute(stmt)).scalars().all()
    items = [JobDescriptionResponse.model_validate(j) for j in jds]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)

@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(JobDescription)
        .options(selectinload(JobDescription.ats_analyses))
        .where(and_(JobDescription.id == jd_id, JobDescription.user_id == current_user.id))
    )
    jd = (await db.execute(stmt)).scalar_one_or_none()
    if not jd:
        raise NotFoundError("Job description not found")
    return JobDescriptionResponse.model_validate(jd)
