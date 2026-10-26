import math
import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DSAAttempt,
    DSAAttemptStatus,
    DSATopic,
    TopicMastery,
)

DIFFICULTY_WEIGHTS = {
    "easy": 1.0,
    "medium": 2.0,
    "hard": 3.5,
}

DECAY_TAU_DAYS = 45.0
DEFAULT_TARGET_POINTS = 12.0

def compute_attempt_evidence(
    status: DSAAttemptStatus,
    difficulty: str,
    confidence: int,
    attempted_at: datetime,
    as_of: datetime | None = None,
) -> float:
    if as_of is None:
        as_of = datetime.now(UTC)
    
    # Delta days >= 0
    delta_sec = max(0.0, (as_of - attempted_at).total_seconds())
    delta_days = delta_sec / 86400.0
    
    decay = math.exp(-delta_days / DECAY_TAU_DAYS)
    weight = DIFFICULTY_WEIGHTS.get(difficulty.lower(), 2.0)
    
    if status == DSAAttemptStatus.SOLVED:
        # Confidence factor c = 0.6 + 0.1 * confidence (confidence in 1..5)
        c = 0.6 + 0.1 * max(1, min(5, confidence))
        return weight * c * decay
    elif status == DSAAttemptStatus.FAILED:
        return -0.5 * weight * decay
    return 0.0

def compute_topic_evidence(attempts: list[DSAAttempt], as_of: datetime | None = None) -> float:
    total_s = 0.0
    for att in attempts:
        total_s += compute_attempt_evidence(
            status=att.status,
            difficulty=att.difficulty,
            confidence=att.confidence,
            attempted_at=att.attempted_at,
            as_of=as_of,
        )
    return total_s

def compute_mastery_from_evidence(evidence_s: float, target_points: float = DEFAULT_TARGET_POINTS) -> float:
    effective_s = max(0.0, evidence_s)
    # mastery = 1 - exp(-max(S, 0) / target_points)
    mastery = 1.0 - math.exp(-effective_s / max(1.0, target_points))
    return max(0.0, min(1.0, mastery))

def compute_topic_priority(
    mastery: float,
    importance: float,
    last_practiced_at: datetime | None,
    as_of: datetime | None = None,
) -> float:
    if as_of is None:
        as_of = datetime.now(UTC)
    
    if last_practiced_at is None:
        days_since = 30.0  # Treat unpracticed as max recency deficit
    else:
        days_since = max(0.0, (as_of - last_practiced_at).total_seconds() / 86400.0)
    
    recency_factor = min(1.0, days_since / 30.0)
    # Priority = (1 - mastery) * importance + 0.1 * min(1, days_since_practice / 30)
    return (1.0 - mastery) * importance + 0.1 * recency_factor

async def recompute_and_save_topic_mastery(
    user_id: uuid.UUID,
    topic_id: uuid.UUID,
    db: AsyncSession,
) -> TopicMastery:
    """Recomputes topic_mastery on every attempt write."""
    # Fetch all attempts for user and topic
    stmt = (
        select(DSAAttempt)
        .where(and_(DSAAttempt.user_id == user_id, DSAAttempt.topic_id == topic_id))
        .order_by(DSAAttempt.attempted_at.asc())
    )
    attempts = (await db.execute(stmt)).scalars().all()

    # Fetch topic for target_points and importance
    topic_stmt = select(DSATopic).where(DSATopic.id == topic_id)
    topic = (await db.execute(topic_stmt)).scalar_one()

    total_s = compute_topic_evidence(attempts)
    mastery_score = compute_mastery_from_evidence(total_s, topic.target_points)
    
    last_practiced = max((a.attempted_at for a in attempts), default=None)

    # Fetch or create TopicMastery record
    tm_stmt = select(TopicMastery).where(
        and_(TopicMastery.user_id == user_id, TopicMastery.topic_id == topic_id)
    )
    tm = (await db.execute(tm_stmt)).scalar_one_or_none()

    evidence_summary = {
        "evidence_s": round(total_s, 4),
        "total_attempts": len(attempts),
        "solved": sum(1 for a in attempts if a.status == DSAAttemptStatus.SOLVED),
        "failed": sum(1 for a in attempts if a.status == DSAAttemptStatus.FAILED),
    }

    if tm is None:
        tm = TopicMastery(
            user_id=user_id,
            topic_id=topic_id,
            mastery=round(mastery_score, 4),
            evidence=evidence_summary,
            last_practiced_at=last_practiced,
        )
        db.add(tm)
    else:
        tm.mastery = round(mastery_score, 4)
        tm.evidence = evidence_summary
        tm.last_practiced_at = last_practiced
        tm.updated_at = datetime.now(UTC)

    await db.flush()
    return tm
