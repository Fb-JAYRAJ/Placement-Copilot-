import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError
from app.models.models import (
    ActivityEvent,
    DSAAttempt,
    DSAAttemptStatus,
    DSAProblem,
    DSATopic,
    ProblemTopic,
    TopicMastery,
    User,
)
from app.schemas.common import PaginatedResponse
from app.schemas.dsa import (
    DSAAttemptCreateRequest,
    DSAAttemptResponse,
    DSAAttemptUpdateRequest,
    DSAProblemResponse,
    DSARecommendationResponse,
    DSAReviewsDueResponse,
    DSATopicResponse,
    TopicMasteryResponse,
)
from app.services.dsa.mastery import recompute_and_save_topic_mastery
from app.services.dsa.recommendations import get_dsa_recommendations
from app.services.dsa.sm2 import calculate_sm2
from app.services.dsa.stats import compute_dsa_stats

router = APIRouter(prefix="/dsa", tags=["dsa"])

@router.get("/topics", response_model=PaginatedResponse[DSATopicResponse])
async def get_topics(db: AsyncSession = Depends(get_db)):
    stmt = select(DSATopic).order_by(DSATopic.importance.desc(), DSATopic.name.asc())
    topics = (await db.execute(stmt)).scalars().all()
    items = [DSATopicResponse.model_validate(t) for t in topics]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)

@router.get("/problems", response_model=PaginatedResponse[DSAProblemResponse])
async def get_problems(
    topic: str | None = Query(None, description="Topic slug or UUID"),
    difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
    q: str | None = Query(None, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DSAProblem).distinct()
    
    if topic:
        # Check if UUID or slug
        try:
            topic_uuid = uuid.UUID(topic)
            stmt = stmt.join(ProblemTopic, ProblemTopic.problem_id == DSAProblem.id).where(
                ProblemTopic.topic_id == topic_uuid
            )
        except ValueError:
            stmt = (
                stmt.join(ProblemTopic, ProblemTopic.problem_id == DSAProblem.id)
                .join(DSATopic, DSATopic.id == ProblemTopic.topic_id)
                .where(DSATopic.slug == topic)
            )

    if difficulty:
        stmt = stmt.where(DSAProblem.difficulty == difficulty.lower())

    if q:
        search_filter = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(DSAProblem.title).like(search_filter),
                func.lower(DSAProblem.slug).like(search_filter),
            )
        )

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(DSAProblem.frequency.desc()).limit(limit).offset(offset)
    problems = (await db.execute(stmt)).scalars().all()

    items = []
    for p in problems:
        # Get associated topic IDs
        t_stmt = select(ProblemTopic.topic_id).where(ProblemTopic.problem_id == p.id)
        topic_ids = (await db.execute(t_stmt)).scalars().all()
        items.append(
            DSAProblemResponse(
                id=p.id,
                slug=p.slug,
                title=p.title,
                difficulty=p.difficulty,
                platform=p.platform,
                url=p.url,
                frequency=p.frequency,
                topic_ids=list(topic_ids),
            )
        )

    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

@router.post("/attempts", response_model=DSAAttemptResponse, status_code=status.HTTP_201_CREATED)
async def create_attempt(
    payload: DSAAttemptCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify topic exists
    topic = (await db.execute(select(DSATopic).where(DSATopic.id == payload.topic_id))).scalar_one_or_none()
    if not topic:
        raise NotFoundError("DSA topic not found")

    problem = None
    if payload.problem_id:
        problem = (await db.execute(select(DSAProblem).where(DSAProblem.id == payload.problem_id))).scalar_one_or_none()
        if not problem:
            raise NotFoundError("DSA problem not found")

    attempt_time = payload.attempted_at or datetime.now(UTC)
    solved_time = attempt_time if payload.status == DSAAttemptStatus.SOLVED else None

    # Calculate initial SM-2
    sm2_quality = payload.confidence if payload.status == DSAAttemptStatus.SOLVED else 1
    reps, ease, interval, next_review = calculate_sm2(
        quality=sm2_quality,
        review_time=attempt_time,
    )

    attempt = DSAAttempt(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        custom_title=payload.custom_title,
        topic_id=payload.topic_id,
        difficulty=payload.difficulty.lower(),
        status=payload.status,
        confidence=payload.confidence,
        time_spent_min=payload.time_spent_min,
        notes=payload.notes,
        attempted_at=attempt_time,
        solved_at=solved_time,
        sm2_ease=ease,
        sm2_interval_days=interval,
        sm2_repetitions=reps,
        next_review_at=next_review,
    )
    db.add(attempt)
    await db.flush()

    # Recompute topic mastery
    await recompute_and_save_topic_mastery(current_user.id, payload.topic_id, db)

    # Activity event
    title_str = problem.title if problem else (payload.custom_title or "DSA Problem")
    action_str = "Solved" if payload.status == DSAAttemptStatus.SOLVED else "Attempted"
    event = ActivityEvent(
        user_id=current_user.id,
        type="dsa_attempt",
        title=f"{action_str} {title_str}",
        detail={
            "difficulty": payload.difficulty,
            "status": payload.status.value,
            "topic": topic.name,
        },
    )
    db.add(event)
    await db.commit()
    await db.refresh(attempt)

    return DSAAttemptResponse(
        id=attempt.id,
        problem_id=attempt.problem_id,
        custom_title=attempt.custom_title,
        topic_id=attempt.topic_id,
        topic_name=topic.name,
        problem_title=problem.title if problem else None,
        difficulty=attempt.difficulty,
        status=attempt.status,
        confidence=attempt.confidence,
        time_spent_min=attempt.time_spent_min,
        notes=attempt.notes,
        attempted_at=attempt.attempted_at,
        solved_at=attempt.solved_at,
        sm2_ease=attempt.sm2_ease,
        sm2_interval_days=attempt.sm2_interval_days,
        sm2_repetitions=attempt.sm2_repetitions,
        next_review_at=attempt.next_review_at,
    )

@router.get("/attempts", response_model=PaginatedResponse[DSAAttemptResponse])
async def get_attempts(
    status: DSAAttemptStatus | None = None,
    topic_id: uuid.UUID | None = None,
    difficulty: str | None = Query(None, pattern="^(easy|medium|hard)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_stmt = select(DSAAttempt).where(DSAAttempt.user_id == current_user.id)
    if status:
        base_stmt = base_stmt.where(DSAAttempt.status == status)
    if topic_id:
        base_stmt = base_stmt.where(DSAAttempt.topic_id == topic_id)
    if difficulty:
        base_stmt = base_stmt.where(DSAAttempt.difficulty == difficulty.lower())

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        base_stmt.options(selectinload(DSAAttempt.topic), selectinload(DSAAttempt.problem))
        .order_by(DSAAttempt.attempted_at.desc())
        .limit(limit)
        .offset(offset)
    )
    attempts = (await db.execute(stmt)).scalars().all()

    items = []
    for a in attempts:
        topic_name = a.topic.name if a.topic else "Unknown Topic"
        prob_title = a.problem.title if a.problem else None
        items.append(
            DSAAttemptResponse(
                id=a.id,
                problem_id=a.problem_id,
                custom_title=a.custom_title,
                topic_id=a.topic_id,
                topic_name=topic_name,
                problem_title=prob_title,
                difficulty=a.difficulty,
                status=a.status,
                confidence=a.confidence,
                time_spent_min=a.time_spent_min,
                notes=a.notes,
                attempted_at=a.attempted_at,
                solved_at=a.solved_at,
                sm2_ease=a.sm2_ease,
                sm2_interval_days=a.sm2_interval_days,
                sm2_repetitions=a.sm2_repetitions,
                next_review_at=a.next_review_at,
            )
        )

    return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

@router.patch("/attempts/{attempt_id}", response_model=DSAAttemptResponse)
async def update_attempt(
    attempt_id: uuid.UUID,
    payload: DSAAttemptUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(DSAAttempt)
        .options(selectinload(DSAAttempt.topic), selectinload(DSAAttempt.problem))
        .where(and_(DSAAttempt.id == attempt_id, DSAAttempt.user_id == current_user.id))
    )
    attempt = (await db.execute(stmt)).scalar_one_or_none()
    if not attempt:
        raise NotFoundError("DSA attempt not found")

    if payload.custom_title is not None:
        attempt.custom_title = payload.custom_title
    if payload.difficulty is not None:
        attempt.difficulty = payload.difficulty.lower()
    if payload.confidence is not None:
        attempt.confidence = payload.confidence
    if payload.time_spent_min is not None:
        attempt.time_spent_min = payload.time_spent_min
    if payload.notes is not None:
        attempt.notes = payload.notes
    
    if payload.status is not None:
        attempt.status = payload.status
        if payload.status == DSAAttemptStatus.SOLVED and not attempt.solved_at:
            attempt.solved_at = datetime.now(UTC)
            # update SM-2
            reps, ease, interval, next_review = calculate_sm2(
                quality=attempt.confidence,
                previous_repetitions=attempt.sm2_repetitions,
                previous_ease=attempt.sm2_ease,
                previous_interval=attempt.sm2_interval_days,
            )
            attempt.sm2_repetitions = reps
            attempt.sm2_ease = ease
            attempt.sm2_interval_days = interval
            attempt.next_review_at = next_review

    await db.flush()
    await recompute_and_save_topic_mastery(current_user.id, attempt.topic_id, db)
    await db.commit()

    refetched = (await db.execute(stmt)).scalar_one()
    topic_name = refetched.topic.name if refetched.topic else "Unknown Topic"
    prob_title = refetched.problem.title if refetched.problem else None

    return DSAAttemptResponse(
        id=attempt.id,
        problem_id=attempt.problem_id,
        custom_title=attempt.custom_title,
        topic_id=attempt.topic_id,
        topic_name=topic_name,
        problem_title=prob_title,
        difficulty=attempt.difficulty,
        status=attempt.status,
        confidence=attempt.confidence,
        time_spent_min=attempt.time_spent_min,
        notes=attempt.notes,
        attempted_at=attempt.attempted_at,
        solved_at=attempt.solved_at,
        sm2_ease=attempt.sm2_ease,
        sm2_interval_days=attempt.sm2_interval_days,
        sm2_repetitions=attempt.sm2_repetitions,
        next_review_at=attempt.next_review_at,
    )

@router.delete("/attempts/{attempt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attempt(
    attempt_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(DSAAttempt).where(
        and_(DSAAttempt.id == attempt_id, DSAAttempt.user_id == current_user.id)
    )
    attempt = (await db.execute(stmt)).scalar_one_or_none()
    if not attempt:
        raise NotFoundError("DSA attempt not found")

    topic_id = attempt.topic_id
    await db.delete(attempt)
    await db.flush()

    await recompute_and_save_topic_mastery(current_user.id, topic_id, db)
    await db.commit()

@router.get("/mastery", response_model=PaginatedResponse[TopicMasteryResponse])
async def get_mastery(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all topics
    topics = (await db.execute(select(DSATopic).order_by(DSATopic.name.asc()))).scalars().all()
    # Fetch user mastery records
    m_stmt = select(TopicMastery).where(TopicMastery.user_id == current_user.id)
    records = {m.topic_id: m for m in (await db.execute(m_stmt)).scalars().all()}

    results = []
    for t in topics:
        tm = records.get(t.id)
        results.append(
            TopicMasteryResponse(
                topic_id=t.id,
                slug=t.slug,
                name=t.name,
                category=t.category,
                importance=t.importance,
                mastery=tm.mastery if tm else 0.0,
                evidence=tm.evidence if tm else None,
                last_practiced_at=tm.last_practiced_at if tm else None,
            )
        )
    return PaginatedResponse(items=results, total=len(results), limit=len(results), offset=0)

@router.get("/recommendations", response_model=PaginatedResponse[DSARecommendationResponse])
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    recs = await get_dsa_recommendations(current_user.id, db)
    items = [DSARecommendationResponse(**r) for r in recs]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)

@router.get("/reviews/due", response_model=PaginatedResponse[DSAReviewsDueResponse])
async def get_reviews_due(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    stmt = (
        select(DSAAttempt)
        .options(selectinload(DSAAttempt.topic), selectinload(DSAAttempt.problem))
        .where(
            and_(
                DSAAttempt.user_id == current_user.id,
                DSAAttempt.status == DSAAttemptStatus.SOLVED,
                DSAAttempt.next_review_at.isnot(None),
                DSAAttempt.next_review_at <= now,
            )
        )
        .order_by(DSAAttempt.next_review_at.asc())
    )
    due_attempts = (await db.execute(stmt)).scalars().all()

    results = []
    for a in due_attempts:
        overdue_days = max(0, int((now - a.next_review_at).total_seconds() / 86400))
        title = a.problem.title if a.problem else (a.custom_title or "Problem")
        topic_name = a.topic.name if a.topic else "General"
        results.append(
            DSAReviewsDueResponse(
                attempt_id=a.id,
                problem_id=a.problem_id,
                title=title,
                topic_name=topic_name,
                difficulty=a.difficulty,
                next_review_at=a.next_review_at,
                overdue_days=overdue_days,
            )
        )
    return PaginatedResponse(items=results, total=len(results), limit=len(results), offset=0)

@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await compute_dsa_stats(current_user.id, db)
