import uuid

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.models.models import ActivityEvent, Resume, User
from app.schemas.ats import ResumeResponse
from app.schemas.common import PaginatedResponse
from app.services.ats.extractor import get_taxonomy_matcher
from app.services.ats.parser import normalize_text, parse_resume_content, parse_sections_and_contact

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile | None = File(None),
    title: str | None = Form(None),
    content_text: str | None = Form(None),
    is_primary: bool | None = Form(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    matcher = get_taxonomy_matcher()

    if file:
        raw_bytes = await file.read()
        filename = file.filename or "uploaded_resume"
        file_type, normalized_text, parsed_sections = parse_resume_content(raw_bytes, filename)
        resume_title = title or filename
    elif content_text:
        if len(content_text.strip()) < 20:
            raise ValidationError("Resume text must be at least 20 characters")
        raw_bytes = content_text.encode("utf-8")
        filename = "pasted_resume.txt"
        file_type = "text"
        normalized_text = normalize_text(content_text)
        parsed_sections = parse_sections_and_contact(normalized_text)
        resume_title = title or "Pasted Resume"
    else:
        raise ValidationError("Either a file or content_text must be provided")

    # Extract skills for stored parsed summary
    extracted_skills = matcher.extract_skills_from_text(normalized_text)
    parsed_sections["skills_detected"] = extracted_skills

    resume = Resume(
        user_id=current_user.id,
        title=resume_title,
        filename=filename,
        file_type=file_type,
        content_text=normalized_text,
        parsed=parsed_sections,
        is_primary=is_primary or False,
    )
    db.add(resume)
    await db.flush()

    event = ActivityEvent(
        user_id=current_user.id,
        type="resume_upload",
        title=f"Uploaded Resume: {resume_title}",
        detail={"file_type": file_type, "word_count": parsed_sections.get("word_count", 0)},
    )
    db.add(event)
    await db.commit()
    await db.refresh(resume)

    return ResumeResponse.model_validate(resume)

@router.get("", response_model=PaginatedResponse[ResumeResponse])
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Resume)
        .options(selectinload(Resume.ats_analyses))
        .where(Resume.user_id == current_user.id)
        .order_by(Resume.created_at.desc())
    )
    resumes = (await db.execute(stmt)).scalars().all()
    items = [ResumeResponse.model_validate(r) for r in resumes]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Resume)
        .options(selectinload(Resume.ats_analyses))
        .where(and_(Resume.id == resume_id, Resume.user_id == current_user.id))
    )
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found")
    return ResumeResponse.model_validate(resume)

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Resume).where(and_(Resume.id == resume_id, Resume.user_id == current_user.id))
    resume = (await db.execute(stmt)).scalar_one_or_none()
    if not resume:
        raise NotFoundError("Resume not found")
    await db.delete(resume)
    await db.commit()
