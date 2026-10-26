from collections import defaultdict
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    InterviewAnswer,
    InterviewQuestion,
    MockInterview,
    MockInterviewStatus,
)


async def generate_interview_report(
    interview: MockInterview,
    questions: list[InterviewQuestion],
    answers: list[InterviewAnswer],
    db: AsyncSession,
) -> dict[str, Any]:
    if not answers:
        return {
            "overall_score": 0.0,
            "final_ability": interview.ability,
            "theta_trajectory": [2.5],
            "per_topic_scores": {},
            "top_gaps": [],
            "action_items": ["Complete at least one interview question to generate a report."],
            "delta_vs_previous": None,
        }

    # 1. Difficulty-weighted overall score
    total_weighted_score = 0.0
    total_weights = 0.0

    topic_scores = defaultdict(list)
    all_gaps = []

    answer_map = {a.question_id: a for a in answers}

    for q in questions:
        ans = answer_map.get(q.id)
        if ans:
            w = max(1.0, q.difficulty)
            total_weighted_score += w * ans.overall
            total_weights += w
            topic_scores[q.topic].append(ans.overall)
            
            feedback = ans.feedback or {}
            if isinstance(feedback, dict) and "gaps" in feedback:
                for g in feedback["gaps"]:
                    if g not in all_gaps:
                        all_gaps.append(g)

    overall_score = round(total_weighted_score / max(1.0, total_weights), 2)

    # 2. Per-topic scores
    per_topic = {}
    for topic_name, scores in topic_scores.items():
        per_topic[topic_name] = {
            "average_score": round(sum(scores) / len(scores), 2),
            "questions_count": len(scores),
        }

    # 3. Top 3 gaps
    top_3_gaps = all_gaps[:3]

    # 4. Grounded action items based on gaps
    action_items = []
    for gap in top_3_gaps:
        action_items.append(f"Review core fundamentals addressing: {gap}")
    
    # Fill up to 3 action items
    weak_topics = sorted(per_topic.items(), key=lambda x: x[1]["average_score"])
    if weak_topics and len(action_items) < 3:
        action_items.append(f"Practice 2-3 medium problems in '{weak_topics[0][0]}' in the DSA Tracker.")
    if len(action_items) < 3:
        action_items.append("Simulate another mock session in this track to benchmark trajectory gains.")

    # 5. Delta vs previous session of same track
    prev_stmt = (
        select(MockInterview)
        .where(
            and_(
                MockInterview.user_id == interview.user_id,
                MockInterview.track == interview.track,
                MockInterview.status == MockInterviewStatus.COMPLETED,
                MockInterview.id != interview.id,
            )
        )
        .order_by(MockInterview.ended_at.desc())
        .limit(1)
    )
    prev_session = (await db.execute(prev_stmt)).scalar_one_or_none()
    delta_vs_prev = None
    if prev_session and prev_session.final_score is not None:
        delta_vs_prev = round(overall_score - prev_session.final_score, 2)

    # Reconstruct theta trajectory from report or history
    existing_report = interview.report or {}
    theta_trajectory = existing_report.get("theta_trajectory", [2.5, interview.ability])

    report_payload = {
        "overall_score": overall_score,
        "final_ability": interview.ability,
        "theta_trajectory": theta_trajectory,
        "per_topic_scores": per_topic,
        "top_gaps": top_3_gaps,
        "action_items": action_items[:3],
        "delta_vs_previous": delta_vs_prev,
    }

    return report_payload
