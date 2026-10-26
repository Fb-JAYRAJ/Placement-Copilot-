import enum
import uuid
from datetime import UTC, date, datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.core.db import Base, BaseModel

# JSON type fallback for cross-engine compatibility if needed
JSON_TYPE = JSONB().with_variant(JSON, "sqlite")
ARRAY_TEXT = ARRAY(String).with_variant(JSON, "sqlite")

# --- Enums ---

class DSAAttemptStatus(enum.StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    SOLVED = "solved"
    FAILED = "failed"

class InterviewTrack(enum.StrEnum):
    DSA_CONCEPTS = "dsa_concepts"
    CS_FUNDAMENTALS = "cs_fundamentals"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"

class MockInterviewStatus(enum.StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class QuestionSource(enum.StrEnum):
    BANK = "bank"
    GENERATED = "generated"
    FOLLOW_UP = "follow_up"


# --- User & Auth ---

class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    college: Mapped[str | None] = mapped_column(String(255), nullable=True)
    grad_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_companies: Mapped[list[str] | None] = mapped_column(ARRAY_TEXT, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    resumes: Mapped[list["Resume"]] = relationship(
        "Resume", back_populates="user", cascade="all, delete-orphan"
    )
    job_descriptions: Mapped[list["JobDescription"]] = relationship(
        "JobDescription", back_populates="user", cascade="all, delete-orphan"
    )
    ats_analyses: Mapped[list["ATSAnalysis"]] = relationship(
        "ATSAnalysis", back_populates="user", cascade="all, delete-orphan"
    )
    dsa_attempts: Mapped[list["DSAAttempt"]] = relationship(
        "DSAAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    mock_interviews: Mapped[list["MockInterview"]] = relationship(
        "MockInterview", back_populates="user", cascade="all, delete-orphan"
    )
    readiness_snapshots: Mapped[list["ReadinessSnapshot"]] = relationship(
        "ReadinessSnapshot", back_populates="user", cascade="all, delete-orphan"
    )
    activity_events: Mapped[list["ActivityEvent"]] = relationship(
        "ActivityEvent", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    family_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=False,
        default=uuid.uuid4,
    )
    successor_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_created", "user_id", "created_at"),
        Index("idx_refresh_tokens_family_id", "family_id"),
    )


# --- Resume, JD & ATS ---

class Resume(BaseModel):
    __tablename__ = "resumes"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="My Resume")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(32), nullable=False)  # pdf, docx, text
    content_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[Any | None] = mapped_column(JSON_TYPE, nullable=True)  # sections, skills with evidence
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="resumes")
    ats_analyses: Mapped[list["ATSAnalysis"]] = relationship(
        "ATSAnalysis", back_populates="resume", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_resumes_user_created", "user_id", "created_at"),
    )


class JobDescription(BaseModel):
    __tablename__ = "job_descriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    jd_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted: Mapped[Any | None] = mapped_column(JSON_TYPE, nullable=True)  # skills with importance

    user: Mapped["User"] = relationship("User", back_populates="job_descriptions")
    ats_analyses: Mapped[list["ATSAnalysis"]] = relationship(
        "ATSAnalysis", back_populates="job_description", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_job_descriptions_user_created", "user_id", "created_at"),
    )


class ATSAnalysis(BaseModel):
    __tablename__ = "ats_analyses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
    )
    jd_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
    )
    overall: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    keyword_score: Mapped[float] = mapped_column(Float, nullable=False)
    semantic_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    tfidf_score: Mapped[float] = mapped_column(Float, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    matched: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    missing: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    suggestions: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="ats_analyses")
    resume: Mapped["Resume"] = relationship("Resume", back_populates="ats_analyses")
    job_description: Mapped["JobDescription"] = relationship("JobDescription", back_populates="ats_analyses")

    __table_args__ = (
        Index("idx_ats_analyses_user_created", "user_id", "created_at"),
    )


# --- DSA Mastery & Problems ---

class DSATopic(BaseModel):
    __tablename__ = "dsa_topics"

    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    importance: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0-1
    target_points: Mapped[float] = mapped_column(Float, default=12.0, nullable=False)

    problems: Mapped[list["DSAProblem"]] = relationship(
        "DSAProblem", secondary="problem_topics", back_populates="topics"
    )


class DSAProblem(BaseModel):
    __tablename__ = "dsa_problems"

    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)  # easy, medium, hard
    platform: Mapped[str] = mapped_column(String(64), default="LeetCode", nullable=False)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    frequency: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0-1

    topics: Mapped[list["DSATopic"]] = relationship(
        "DSATopic", secondary="problem_topics", back_populates="problems"
    )


class ProblemTopic(Base):
    __tablename__ = "problem_topics"

    problem_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dsa_problems.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dsa_topics.id", ondelete="CASCADE"),
        primary_key=True,
    )


class DSAAttempt(BaseModel):
    __tablename__ = "dsa_attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dsa_problems.id", ondelete="SET NULL"),
        nullable=True,
    )
    custom_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dsa_topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    difficulty: Mapped[str] = mapped_column(String(32), nullable=False)  # easy, medium, hard
    status: Mapped[DSAAttemptStatus] = mapped_column(
        Enum(DSAAttemptStatus, name="dsa_attempt_status_enum", native_enum=False),
        nullable=False,
    )
    confidence: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1-5
    time_spent_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    solved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sm2_ease: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    sm2_interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    sm2_repetitions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="dsa_attempts")
    topic: Mapped["DSATopic"] = relationship("DSATopic")
    problem: Mapped[Optional["DSAProblem"]] = relationship("DSAProblem")

    __table_args__ = (
        Index("idx_dsa_attempts_user_created", "user_id", "created_at"),
    )


class TopicMastery(Base):
    __tablename__ = "topic_mastery"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("dsa_topics.id", ondelete="CASCADE"),
        primary_key=True,
    )
    mastery: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-1
    evidence: Mapped[Any | None] = mapped_column(JSON_TYPE, nullable=True)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User")
    topic: Mapped["DSATopic"] = relationship("DSATopic")


# --- Question Bank & Mock Interview ---

class QuestionBank(BaseModel):
    __tablename__ = "question_bank"

    track: Mapped[InterviewTrack] = mapped_column(
        Enum(InterviewTrack, name="interview_track_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    topic: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_points: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)


class MockInterview(BaseModel):
    __tablename__ = "mock_interviews"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    track: Mapped[InterviewTrack] = mapped_column(
        Enum(InterviewTrack, name="interview_track_enum", native_enum=False),
        nullable=False,
    )
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    planned_questions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    status: Mapped[MockInterviewStatus] = mapped_column(
        Enum(MockInterviewStatus, name="mock_interview_status_enum", native_enum=False),
        default=MockInterviewStatus.ACTIVE,
        nullable=False,
    )
    ability: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)  # theta in [1, 5]
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-10
    report: Mapped[Any | None] = mapped_column(JSON_TYPE, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="mock_interviews")
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        "InterviewQuestion", back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.seq"
    )

    __table_args__ = (
        Index("idx_mock_interviews_user_created", "user_id", "created_at"),
    )


class InterviewQuestion(BaseModel):
    __tablename__ = "interview_questions"

    interview_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("mock_interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    topic: Mapped[str] = mapped_column(String(128), nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, nullable=False)  # b in [1, 5]
    text: Mapped[str] = mapped_column(Text, nullable=False)
    ideal_points: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)
    source: Mapped[QuestionSource] = mapped_column(
        Enum(QuestionSource, name="question_source_enum", native_enum=False),
        default=QuestionSource.BANK,
        nullable=False,
    )
    parent_question_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="SET NULL"),
        nullable=True,
    )

    interview: Mapped["MockInterview"] = relationship("MockInterview", back_populates="questions")
    answer: Mapped[Optional["InterviewAnswer"]] = relationship(
        "InterviewAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )


class InterviewAnswer(BaseModel):
    __tablename__ = "interview_answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("interview_questions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    scores: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)  # correctness, depth, structure, communication
    overall: Mapped[float] = mapped_column(Float, nullable=False)  # 0-10
    feedback: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)  # strengths, gaps, improved_answer
    time_taken_sec: Mapped[int | None] = mapped_column(Integer, nullable=True)
    degraded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    question: Mapped["InterviewQuestion"] = relationship("InterviewQuestion", back_populates="answer")


# --- Readiness & Activity ---

class ReadinessSnapshot(BaseModel):
    __tablename__ = "readiness_snapshots"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ats: Mapped[float | None] = mapped_column(Float, nullable=True)
    dsa: Mapped[float | None] = mapped_column(Float, nullable=True)
    interview: Mapped[float | None] = mapped_column(Float, nullable=True)
    consistency: Mapped[float] = mapped_column(Float, nullable=False)
    composite: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # share of weight with data
    explanation: Mapped[Any] = mapped_column(JSON_TYPE, nullable=False)  # levers, breakdown

    user: Mapped["User"] = relationship("User", back_populates="readiness_snapshots")

    __table_args__ = (
        Index("idx_readiness_snapshots_user_created", "user_id", "created_at"),
    )


class ActivityEvent(BaseModel):
    __tablename__ = "activity_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # ats_run, dsa_attempt, mock_session, etc.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    detail: Mapped[Any | None] = mapped_column(JSON_TYPE, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="activity_events")

    __table_args__ = (
        Index("idx_activity_events_user_created", "user_id", "created_at"),
    )


class LLMUsage(BaseModel):
    __tablename__ = "llm_usage"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_llm_usage_user_day"),
        Index("idx_llm_usage_user_created", "user_id", "created_at"),
    )
