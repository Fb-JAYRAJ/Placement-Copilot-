import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.core.errors import NotFoundError, ValidationError
from app.core.ratelimit import check_and_increment_llm_quota, limiter
from app.models.models import (
    ActivityEvent,
    InterviewAnswer,
    InterviewQuestion,
    MockInterview,
    MockInterviewStatus,
    QuestionSource,
    User,
)
from app.schemas.common import PaginatedResponse
from app.schemas.interview import (
    InterviewAnswerResponse,
    InterviewAnswerSubmitRequest,
    InterviewCreateRequest,
    InterviewQuestionResponse,
    InterviewReportResponse,
    InterviewResponse,
    InterviewSubmitAnswerResult,
)
from app.services.interview.adaptive import (
    select_or_generate_next_question,
    update_ability,
)
from app.services.interview.evaluator import evaluate_interview_answer
from app.services.interview.report import generate_interview_report

router = APIRouter(prefix="/interviews", tags=["interviews"])

@router.post("", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    interview = MockInterview(
        user_id=current_user.id,
        track=payload.track,
        company=payload.company,
        role=payload.role,
        planned_questions=payload.planned_questions,
        status=MockInterviewStatus.ACTIVE,
        ability=2.5,
        report={"theta_trajectory": [2.5]},
    )
    db.add(interview)
    await db.flush()

    # Select Question 1
    text, topic, difficulty, ideal_points, source = await select_or_generate_next_question(
        interview=interview,
        existing_questions=[],
        db=db,
    )

    q1 = InterviewQuestion(
        interview_id=interview.id,
        seq=1,
        topic=topic,
        difficulty=difficulty,
        text=text,
        ideal_points=ideal_points,
        source=source,
    )
    db.add(q1)

    event = ActivityEvent(
        user_id=current_user.id,
        type="mock_interview_start",
        title=f"Started {payload.track.value.replace('_', ' ').title()} Mock Interview",
        detail={"planned_questions": payload.planned_questions, "company": payload.company},
    )
    db.add(event)
    await db.commit()
    await db.refresh(interview)
    await db.refresh(q1)

    return InterviewResponse(
        id=interview.id,
        track=interview.track,
        company=interview.company,
        role=interview.role,
        planned_questions=interview.planned_questions,
        status=interview.status,
        ability=interview.ability,
        final_score=interview.final_score,
        current_question=InterviewQuestionResponse.model_validate(q1),
        questions_answered_count=0,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
    )

@router.get("", response_model=PaginatedResponse[InterviewResponse])
async def list_interviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MockInterview)
        .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
        .where(MockInterview.user_id == current_user.id)
        .order_by(MockInterview.started_at.desc())
    )
    interviews = (await db.execute(stmt)).scalars().all()
    results = []
    for iv in interviews:
        answered_count = sum(1 for q in iv.questions if q.answer)

        results.append(
            InterviewResponse(
                id=iv.id,
                track=iv.track,
                company=iv.company,
                role=iv.role,
                planned_questions=iv.planned_questions,
                status=iv.status,
                ability=iv.ability,
                final_score=iv.final_score,
                questions_answered_count=answered_count,
                started_at=iv.started_at,
                ended_at=iv.ended_at,
            )
        )
    return PaginatedResponse(items=results, total=len(results), limit=len(results), offset=0)

@router.get("/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MockInterview)
        .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
        .where(and_(MockInterview.id == interview_id, MockInterview.user_id == current_user.id))
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview:
        raise NotFoundError("Mock interview not found")

    questions = interview.questions
    current_q = None
    answered_count = 0
    for q in questions:
        if q.answer:
            answered_count += 1
        elif current_q is None:
            current_q = q

    return InterviewResponse(
        id=interview.id,
        track=interview.track,
        company=interview.company,
        role=interview.role,
        planned_questions=interview.planned_questions,
        status=interview.status,
        ability=interview.ability,
        final_score=interview.final_score,
        current_question=InterviewQuestionResponse.model_validate(current_q) if current_q else None,
        questions_answered_count=answered_count,
        started_at=interview.started_at,
        ended_at=interview.ended_at,
    )

@router.post("/{interview_id}/answers", response_model=InterviewSubmitAnswerResult)
@limiter.limit("20/minute")
async def submit_answer(
    request: Request,
    interview_id: uuid.UUID,
    payload: InterviewAnswerSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MockInterview).where(
        and_(MockInterview.id == interview_id, MockInterview.user_id == current_user.id)
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview:
        raise NotFoundError("Mock interview not found")

    if interview.status != MockInterviewStatus.ACTIVE:
        raise ValidationError("This interview session has already ended")

    # Fetch question
    q_stmt = select(InterviewQuestion).where(
        and_(
            InterviewQuestion.id == payload.question_id,
            InterviewQuestion.interview_id == interview.id,
        )
    )
    question = (await db.execute(q_stmt)).scalar_one_or_none()
    if not question:
        raise NotFoundError("Interview question not found")

    # Check if already answered
    existing_a = (
        await db.execute(select(InterviewAnswer).where(InterviewAnswer.question_id == question.id))
    ).scalar_one_or_none()
    if existing_a:
        raise ValidationError("This question has already been answered")

    # LLM Quota tracking
    await check_and_increment_llm_quota(current_user.id, db)

    # Evaluate answer
    eval_dict = await evaluate_interview_answer(
        track=interview.track,
        question_text=question.text,
        ideal_points=question.ideal_points if isinstance(question.ideal_points, list) else [],
        raw_answer=payload.answer_text,
    )

    answer = InterviewAnswer(
        question_id=question.id,
        answer_text=payload.answer_text,
        scores=eval_dict["scores"],
        overall=eval_dict["overall"],
        feedback={
            "strengths": eval_dict["strengths"],
            "gaps": eval_dict["gaps"],
            "improved_answer": eval_dict["improved_answer"],
            "follow_up_question": eval_dict.get("follow_up_question"),
        },
        time_taken_sec=payload.time_taken_sec,
        degraded=eval_dict["degraded"],
    )
    db.add(answer)
    await db.flush()

    # Update ability theta
    new_theta = update_ability(
        theta=interview.ability,
        difficulty=question.difficulty,
        actual_overall_score=eval_dict["overall"],
        question_number=question.seq,
    )
    interview.ability = new_theta

    report_data = interview.report or {}
    trajectory = report_data.get("theta_trajectory", [2.5])
    trajectory.append(new_theta)
    report_data["theta_trajectory"] = trajectory
    interview.report = report_data

    # Fetch all questions and answers in session
    all_q = (
        await db.execute(
            select(InterviewQuestion)
            .where(InterviewQuestion.interview_id == interview.id)
            .order_by(InterviewQuestion.seq.asc())
        )
    ).scalars().all()

    q_ids = [q.id for q in all_q]
    all_ans = (
        await db.execute(select(InterviewAnswer).where(InterviewAnswer.question_id.in_(q_ids)))
    ).scalars().all()

    # Check if session completed
    if len(all_ans) >= interview.planned_questions:
        interview.status = MockInterviewStatus.COMPLETED
        interview.ended_at = datetime.now(UTC)

        final_rep = await generate_interview_report(interview, all_q, all_ans, db)
        interview.final_score = final_rep["overall_score"]
        interview.report = final_rep

        event = ActivityEvent(
            user_id=current_user.id,
            type="mock_interview_completed",
            title=f"Completed {interview.track.value.replace('_', ' ').title()} Mock Interview",
            detail={"overall_score": final_rep["overall_score"], "final_ability": new_theta},
        )
        db.add(event)
        await db.commit()

        return InterviewSubmitAnswerResult(
            evaluation=InterviewAnswerResponse.model_validate(answer),
            next_question=None,
            completed=True,
            final_score=interview.final_score,
            report=InterviewReportResponse(**final_rep),
        )
    else:
        # Generate next question
        next_text, next_topic, next_diff, next_ideal, next_source = await select_or_generate_next_question(
            interview=interview,
            existing_questions=all_q,
            db=db,
        )
        next_q = InterviewQuestion(
            interview_id=interview.id,
            seq=len(all_q) + 1,
            topic=next_topic,
            difficulty=next_diff,
            text=next_text,
            ideal_points=next_ideal,
            source=next_source,
        )
        db.add(next_q)
        await db.commit()
        await db.refresh(next_q)

        return InterviewSubmitAnswerResult(
            evaluation=InterviewAnswerResponse.model_validate(answer),
            next_question=InterviewQuestionResponse.model_validate(next_q),
            completed=False,
            final_score=None,
            report=None,
        )

@router.post("/{interview_id}/follow-up", response_model=InterviewQuestionResponse)
async def create_follow_up(
    interview_id: uuid.UUID,
    question_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(MockInterview).where(
        and_(MockInterview.id == interview_id, MockInterview.user_id == current_user.id)
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview or interview.status != MockInterviewStatus.ACTIVE:
        raise NotFoundError("Active mock interview not found")

    q_stmt = select(InterviewQuestion).where(
        and_(InterviewQuestion.id == question_id, InterviewQuestion.interview_id == interview.id)
    )
    parent_q = (await db.execute(q_stmt)).scalar_one_or_none()
    if not parent_q:
        raise NotFoundError("Parent interview question not found")

    # One follow-up per question
    f_stmt = select(InterviewQuestion).where(InterviewQuestion.parent_question_id == parent_q.id)
    existing_f = (await db.execute(f_stmt)).scalar_one_or_none()
    if existing_f:
        raise ValidationError("A follow-up question has already been asked for this question")

    # Fetch answer to get follow-up text
    a_stmt = select(InterviewAnswer).where(InterviewAnswer.question_id == parent_q.id)
    answer = (await db.execute(a_stmt)).scalar_one_or_none()
    follow_up_text = None
    if answer and answer.feedback and isinstance(answer.feedback, dict):
        follow_up_text = answer.feedback.get("follow_up_question")

    if not follow_up_text:
        follow_up_text = "Can you elaborate on how your approach scales and behaves under high concurrency or failure modes?"

    # Count all questions
    count_stmt = select(InterviewQuestion).where(InterviewQuestion.interview_id == interview.id)
    all_q = (await db.execute(count_stmt)).scalars().all()

    follow_up_q = InterviewQuestion(
        interview_id=interview.id,
        seq=len(all_q) + 1,
        topic=parent_q.topic,
        difficulty=parent_q.difficulty,  # same difficulty
        text=follow_up_text,
        ideal_points=["Scalability considerations", "Failure handling", "Performance trade-offs"],
        source=QuestionSource.FOLLOW_UP,
        parent_question_id=parent_q.id,
    )
    db.add(follow_up_q)
    await db.commit()
    await db.refresh(follow_up_q)

    return InterviewQuestionResponse.model_validate(follow_up_q)

@router.post("/{interview_id}/finish", response_model=InterviewReportResponse)
async def finish_interview(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MockInterview)
        .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
        .where(and_(MockInterview.id == interview_id, MockInterview.user_id == current_user.id))
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview:
        raise NotFoundError("Mock interview not found")

    questions = interview.questions
    answers = [q.answer for q in questions if q.answer is not None]

    report_payload = await generate_interview_report(interview, questions, answers, db)
    
    interview.status = MockInterviewStatus.COMPLETED if answers else MockInterviewStatus.ABANDONED
    interview.final_score = report_payload["overall_score"]
    interview.report = report_payload
    interview.ended_at = datetime.now(UTC)
    await db.commit()

    return InterviewReportResponse(**report_payload)

@router.get("/{interview_id}/report", response_model=InterviewReportResponse)
async def get_report(
    interview_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(MockInterview)
        .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
        .where(and_(MockInterview.id == interview_id, MockInterview.user_id == current_user.id))
    )
    interview = (await db.execute(stmt)).scalar_one_or_none()
    if not interview:
        raise NotFoundError("Mock interview not found")

    if interview.report and isinstance(interview.report, dict) and "overall_score" in interview.report:
        return InterviewReportResponse(**interview.report)

    # Reconstruct report if not cached
    questions = interview.questions
    answers = [q.answer for q in questions if q.answer is not None]

    report_payload = await generate_interview_report(interview, questions, answers, db)
    return InterviewReportResponse(**report_payload)
