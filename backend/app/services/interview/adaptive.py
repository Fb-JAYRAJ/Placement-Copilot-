import math

from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    InterviewQuestion,
    MockInterview,
    QuestionBank,
    QuestionSource,
)
from app.services.llm.provider import get_llm_provider


class GeneratedQuestion(BaseModel):
    topic: str
    difficulty: float
    text: str
    ideal_points: list[str]

def calculate_expected_score(theta: float, difficulty: float) -> float:
    """Logistic IRT model: P = 1 / (1 + e^-(theta - b))"""
    diff = theta - difficulty
    # Avoid overflow in exp
    if diff > 20:
        return 1.0
    elif diff < -20:
        return 0.0
    return 1.0 / (1.0 + math.exp(-diff))

def update_ability(theta: float, difficulty: float, actual_overall_score: float, question_number: int) -> float:
    """
    actual_overall_score is 0 to 10 -> s = overall / 10 in [0, 1].
    K_n = max(0.4, 1.6 * 0.85^(n - 1))
    theta <- clip(theta + K_n * (s - P), 1, 5)
    """
    s = max(0.0, min(10.0, actual_overall_score)) / 10.0
    p = calculate_expected_score(theta, difficulty)
    
    n = max(1, question_number)
    k_n = max(0.4, 1.6 * math.pow(0.85, n - 1))
    
    new_theta = theta + k_n * (s - p)
    return round(max(1.0, min(5.0, new_theta)), 3)

def get_next_target_difficulty(theta: float) -> float:
    """Next target difficulty b* = clip(theta + 0.3, 1, 5)"""
    return round(max(1.0, min(5.0, theta + 0.3)), 2)

async def select_or_generate_next_question(
    interview: MockInterview,
    existing_questions: list[InterviewQuestion],
    db: AsyncSession,
) -> tuple[str, str, float, list[str], QuestionSource]:
    """
    Selects or generates next question:
    - Within +-0.5 of b*
    - Track matching
    - Unasked in session
    - Never same topic twice in a row
    - Covers >= min(4, planned) distinct topics
    - Falls back to schema-validated LLM generation if nothing fits in bank.
    Returns: (text, topic, difficulty, ideal_points, source)
    """
    theta = interview.ability
    b_star = get_next_target_difficulty(theta)
    b_min = max(1.0, b_star - 0.5)
    b_max = min(5.0, b_star + 0.5)

    last_topic = existing_questions[-1].topic if existing_questions else None
    asked_texts = set(q.text for q in existing_questions)
    distinct_topics_used = set(q.topic for q in existing_questions)
    target_distinct_topics = min(4, interview.planned_questions)

    # 1. Query bank for matching questions
    stmt = select(QuestionBank).where(
        and_(
            QuestionBank.track == interview.track,
            QuestionBank.difficulty >= int(b_min),
            QuestionBank.difficulty <= int(math.ceil(b_max)),
        )
    )
    candidates = (await db.execute(stmt)).scalars().all()

    # Filter out asked questions and avoid immediate same topic
    valid_candidates = [
        c for c in candidates
        if c.question_text not in asked_texts and c.topic != last_topic
    ]

    # Prioritize new topics if we haven't met target distinct topics yet
    if len(distinct_topics_used) < target_distinct_topics:
        novel_topic_candidates = [c for c in valid_candidates if c.topic not in distinct_topics_used]
        if novel_topic_candidates:
            valid_candidates = novel_topic_candidates

    if valid_candidates:
        # Pick candidate closest to b_star
        best = min(valid_candidates, key=lambda c: abs(c.difficulty - b_star))
        return (
            best.question_text,
            best.topic,
            float(best.difficulty),
            best.ideal_points if isinstance(best.ideal_points, list) else [],
            QuestionSource.BANK,
        )

    # 2. Bank exhausted or constrained: Generate via LLM under constraints
    provider = get_llm_provider()
    company_context = f" for candidate targeting {interview.company or 'Tech Firm'}"
    role_context = f" in a {interview.role or 'Software Engineer'} role"

    prompt = f"""Generate a high-quality technical interview question.
Track: {interview.track.value}
Target Difficulty: {b_star} (on a scale of 1.0 to 5.0)
Avoid Topic: {last_topic or 'None'}
Context:{company_context}{role_context}

Return valid JSON matching the schema with:
- topic: specific sub-domain
- difficulty: float between 1.0 and 5.0
- text: precise technical interview question
- ideal_points: 3 to 5 key technical points expected in an optimal answer
"""
    system_instruction = "You are a senior technical interviewer. Generate rigorous, precise interview questions with clear rubric ideal points."

    try:
        gen = await provider.generate_json(
            prompt=prompt,
            schema=GeneratedQuestion,
            system_instruction=system_instruction,
        )
        return (
            gen.text,
            gen.topic,
            max(1.0, min(5.0, gen.difficulty)),
            gen.ideal_points,
            QuestionSource.GENERATED,
        )
    except Exception:
        # Fallback to general bank question
        fallback_stmt = select(QuestionBank).where(
            and_(
                QuestionBank.track == interview.track,
                QuestionBank.question_text.notin_(asked_texts),
            )
        ).limit(1)
        fallback = (await db.execute(fallback_stmt)).scalar_one_or_none()
        if fallback:
            return (
                fallback.question_text,
                fallback.topic,
                float(fallback.difficulty),
                fallback.ideal_points if isinstance(fallback.ideal_points, list) else [],
                QuestionSource.BANK,
            )
        
        # Last resort synthetic question
        return (
            f"Explain how you would architect and optimize data access in {interview.track.value}.",
            "Core Concepts",
            b_star,
            ["Time and space complexity", "Concurrency safety", "Trade-offs"],
            QuestionSource.GENERATED,
        )
