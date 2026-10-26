import uuid
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    DSAAttempt,
    DSAAttemptStatus,
    DSAProblem,
    DSATopic,
    ProblemTopic,
    TopicMastery,
)
from app.services.dsa.mastery import compute_topic_priority


async def get_dsa_recommendations(user_id: uuid.UUID, db: AsyncSession, limit: int = 5) -> list[dict[str, Any]]:
    # 1. Fetch all topics
    topics = (await db.execute(select(DSATopic))).scalars().all()
    if not topics:
        return []

    # 2. Fetch existing user mastery records
    mastery_stmt = select(TopicMastery).where(TopicMastery.user_id == user_id)
    mastery_records = {m.topic_id: m for m in (await db.execute(mastery_stmt)).scalars().all()}

    # 3. Compute priority for each topic
    topic_priorities = []
    for topic in topics:
        tm = mastery_records.get(topic.id)
        mastery_val = tm.mastery if tm else 0.0
        last_practiced = tm.last_practiced_at if tm else None
        priority = compute_topic_priority(mastery_val, topic.importance, last_practiced)
        topic_priorities.append((priority, topic, mastery_val))

    # Sort descending by priority
    topic_priorities.sort(key=lambda x: x[0], reverse=True)
    top_3_topics = topic_priorities[:3]

    # 4. Fetch all problem IDs already solved by user
    solved_stmt = select(DSAAttempt.problem_id).where(
        and_(
            DSAAttempt.user_id == user_id,
            DSAAttempt.problem_id.isnot(None),
            DSAAttempt.status == DSAAttemptStatus.SOLVED,
        )
    )
    solved_problem_ids = set((await db.execute(solved_stmt)).scalars().all())

    # 5. For each top topic, find unsolved problems matching mastery band:
    # < 0.3 -> easy or medium
    # 0.3 - 0.7 -> medium
    # > 0.7 -> hard
    topic_problem_queues: dict[uuid.UUID, list[DSAProblem]] = {}

    for _, topic, mastery_val in top_3_topics:
        if mastery_val < 0.3:
            allowed_diffs = ["easy", "medium"]
            reason_template = f"Foundation building in {topic.name} (mastery {int(mastery_val * 100)}%)"
        elif mastery_val <= 0.7:
            allowed_diffs = ["medium"]
            reason_template = f"Strengthen core patterns in {topic.name} (mastery {int(mastery_val * 100)}%)"
        else:
            allowed_diffs = ["hard"]
            reason_template = f"High-frequency mastery challenge in {topic.name} (mastery {int(mastery_val * 100)}%)"

        query = (
            select(DSAProblem)
            .join(ProblemTopic, ProblemTopic.problem_id == DSAProblem.id)
            .where(
                and_(
                    ProblemTopic.topic_id == topic.id,
                    DSAProblem.difficulty.in_(allowed_diffs),
                )
            )
            .order_by(DSAProblem.frequency.desc())
        )
        candidates = (await db.execute(query)).scalars().all()
        # Filter out already solved
        unsolved = [p for p in candidates if p.id not in solved_problem_ids]
        
        # Fallback if no problems in exact band: allow any difficulty
        if not unsolved:
            fallback_query = (
                select(DSAProblem)
                .join(ProblemTopic, ProblemTopic.problem_id == DSAProblem.id)
                .where(ProblemTopic.topic_id == topic.id)
                .order_by(DSAProblem.frequency.desc())
            )
            fallback_candidates = (await db.execute(fallback_query)).scalars().all()
            unsolved = [p for p in fallback_candidates if p.id not in solved_problem_ids]

        topic_problem_queues[topic.id] = (unsolved, reason_template, topic.name)

    # 6. Interleave top 3 priority topics until we have 5 recommendations
    recommendations = []
    seen_problem_ids = set()

    for idx in range(10):  # round-robin rounds
        for _, topic, _ in top_3_topics:
            if len(recommendations) >= limit:
                break
            queue, reason, topic_name = topic_problem_queues[topic.id]
            while queue:
                candidate = queue.pop(0)
                if candidate.id not in seen_problem_ids:
                    seen_problem_ids.add(candidate.id)
                    recommendations.append({
                        "problem_id": str(candidate.id),
                        "slug": candidate.slug,
                        "title": candidate.title,
                        "difficulty": candidate.difficulty,
                        "topic_name": topic_name,
                        "frequency": candidate.frequency,
                        "reason": reason,
                    })
                    break

        if len(recommendations) >= limit:
            break

    return recommendations[:limit]
