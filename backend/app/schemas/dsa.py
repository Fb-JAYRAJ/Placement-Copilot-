import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import DSAAttemptStatus


class DSATopicResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    category: str
    importance: float
    target_points: float

    model_config = ConfigDict(from_attributes=True)

class DSAProblemResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    difficulty: str
    platform: str
    url: str | None = None
    frequency: float
    topic_ids: list[uuid.UUID] = []

    model_config = ConfigDict(from_attributes=True)

class DSAAttemptCreateRequest(BaseModel):
    problem_id: uuid.UUID | None = None
    custom_title: str | None = None
    topic_id: uuid.UUID
    difficulty: str = Field(..., pattern="^(easy|medium|hard)$")
    status: DSAAttemptStatus
    confidence: int = Field(default=3, ge=1, le=5)
    time_spent_min: int | None = Field(None, ge=1)
    notes: str | None = None
    attempted_at: datetime | None = None

class DSAAttemptUpdateRequest(BaseModel):
    custom_title: str | None = None
    difficulty: str | None = Field(None, pattern="^(easy|medium|hard)$")
    status: DSAAttemptStatus | None = None
    confidence: int | None = Field(None, ge=1, le=5)
    time_spent_min: int | None = Field(None, ge=1)
    notes: str | None = None

class DSAAttemptResponse(BaseModel):
    id: uuid.UUID
    problem_id: uuid.UUID | None = None
    custom_title: str | None = None
    topic_id: uuid.UUID
    topic_name: str | None = None
    problem_title: str | None = None
    difficulty: str
    status: DSAAttemptStatus
    confidence: int
    time_spent_min: int | None = None
    notes: str | None = None
    attempted_at: datetime
    solved_at: datetime | None = None
    sm2_ease: float
    sm2_interval_days: int
    sm2_repetitions: int
    next_review_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class TopicMasteryResponse(BaseModel):
    topic_id: uuid.UUID
    slug: str
    name: str
    category: str
    importance: float
    mastery: float  # 0 to 1
    evidence: Any | None = None
    last_practiced_at: datetime | None = None

class DSARecommendationResponse(BaseModel):
    problem_id: str
    slug: str
    title: str
    difficulty: str
    topic_name: str
    frequency: float
    reason: str

class DSAReviewsDueResponse(BaseModel):
    attempt_id: uuid.UUID
    problem_id: uuid.UUID | None = None
    title: str
    topic_name: str
    difficulty: str
    next_review_at: datetime
    overdue_days: int
