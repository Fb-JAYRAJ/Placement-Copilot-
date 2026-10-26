import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.models import InterviewTrack, MockInterviewStatus, QuestionSource


class InterviewCreateRequest(BaseModel):
    track: InterviewTrack
    company: str | None = None
    role: str | None = None
    planned_questions: int = Field(default=5, ge=3, le=15)

class InterviewQuestionResponse(BaseModel):
    id: uuid.UUID
    interview_id: uuid.UUID
    seq: int
    topic: str
    difficulty: float
    text: str
    ideal_points: list[str] = []
    source: QuestionSource
    parent_question_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)

class InterviewAnswerSubmitRequest(BaseModel):
    question_id: uuid.UUID
    answer_text: str = Field(..., min_length=10, max_length=4000)
    time_taken_sec: int | None = Field(None, ge=1)

class InterviewAnswerResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    overall: float
    scores: dict[str, Any]
    feedback: dict[str, Any]
    time_taken_sec: int | None = None
    degraded: bool

    model_config = ConfigDict(from_attributes=True)

class InterviewResponse(BaseModel):
    id: uuid.UUID
    track: InterviewTrack
    company: str | None = None
    role: str | None = None
    planned_questions: int
    status: MockInterviewStatus
    ability: float
    final_score: float | None = None
    current_question: InterviewQuestionResponse | None = None
    questions_answered_count: int = 0
    started_at: datetime
    ended_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class InterviewReportResponse(BaseModel):
    overall_score: float
    final_ability: float
    theta_trajectory: list[float]
    per_topic_scores: dict[str, Any]
    top_gaps: list[str]
    action_items: list[str]
    delta_vs_previous: float | None = None

class InterviewSubmitAnswerResult(BaseModel):
    evaluation: InterviewAnswerResponse
    next_question: InterviewQuestionResponse | None = None
    completed: bool
    final_score: float | None = None
    report: InterviewReportResponse | None = None
