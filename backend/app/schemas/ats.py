import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResumeCreateRequest(BaseModel):
    title: str | None = "My Resume"
    content_text: str = Field(..., min_length=20)
    is_primary: bool | None = False

class ResumeResponse(BaseModel):
    id: uuid.UUID
    title: str
    filename: str
    file_type: str
    is_primary: bool
    parsed: Any | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobDescriptionCreateRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=150)
    role: str = Field(..., min_length=1, max_length=150)
    jd_text: str = Field(..., min_length=20)

class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    company: str
    role: str
    jd_text: str
    extracted: Any | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ATSAnalyzeRequest(BaseModel):
    resume_id: uuid.UUID
    jd_id: uuid.UUID | None = None
    inline_jd_text: str | None = None
    company: str | None = "Target Company"
    role: str | None = "Software Engineer"

class ATSAnalysisResponse(BaseModel):
    id: uuid.UUID
    resume_id: uuid.UUID
    jd_id: uuid.UUID
    overall: float
    keyword_score: float
    semantic_score: float | None = None
    tfidf_score: float
    quality_score: float
    matched: Any
    missing: Any
    suggestions: Any
    degraded: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
