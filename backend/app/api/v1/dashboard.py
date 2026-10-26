from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.db import get_db
from app.core.dependencies import get_current_user
from app.models.models import (
    ActivityEvent,
    ATSAnalysis,
    DSAAttempt,
    DSAAttemptStatus,
    DSATopic,
    InterviewQuestion,
    MockInterview,
    MockInterviewStatus,
    ReadinessSnapshot,
    Resume,
    TopicMastery,
    User,
)
from app.schemas.common import PaginatedResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    ReadinessHistoryResponse,
    ReadinessLeverResponse,
    SparklinePoint,
)
from app.services.readiness.calculator import (
    calculate_ats_component,
    calculate_composite_readiness,
    calculate_consistency_component,
    calculate_dsa_component,
    calculate_interview_component,
    simulate_levers,
)
from app.services.readiness.focus_task import determine_daily_focus_task

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    time_range: str = Query("30d", alias="range", pattern="^(7d|30d|90d)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(UTC)
    today = date.today()

    days_lookup = {"7d": 7, "30d": 30, "90d": 90}
    num_days = days_lookup.get(time_range, 30)

    # 1. Fetch user data across pillars with eager loaded relationships
    ats_stmt = (
        select(ATSAnalysis)
        .options(selectinload(ATSAnalysis.resume), selectinload(ATSAnalysis.job_description))
        .where(ATSAnalysis.user_id == current_user.id)
        .order_by(ATSAnalysis.created_at.desc())
    )
    all_ats = (await db.execute(ats_stmt)).scalars().all()

    topics = (await db.execute(select(DSATopic))).scalars().all()
    total_topics_count = len(topics)

    m_stmt = select(TopicMastery).where(TopicMastery.user_id == current_user.id)
    masteries = {m.topic_id: m.mastery for m in (await db.execute(m_stmt)).scalars().all()}

    att_stmt = (
        select(DSAAttempt)
        .options(selectinload(DSAAttempt.topic), selectinload(DSAAttempt.problem))
        .where(DSAAttempt.user_id == current_user.id)
        .order_by(DSAAttempt.attempted_at.asc())
    )
    attempts = (await db.execute(att_stmt)).scalars().all()

    iv_stmt = (
        select(MockInterview)
        .options(selectinload(MockInterview.questions).selectinload(InterviewQuestion.answer))
        .where(MockInterview.user_id == current_user.id)
        .order_by(MockInterview.started_at.desc())
    )
    interviews = (await db.execute(iv_stmt)).scalars().all()

    # Active dates for consistency
    all_active_dates = set(a.attempted_at.date() for a in attempts)
    for a in all_ats:
        all_active_dates.add(a.created_at.date())
    for iv in interviews:
        all_active_dates.add(iv.started_at.date())

    # Current streak
    sorted_active = sorted(all_active_dates)
    current_streak = 0
    if sorted_active:
        chk = today
        if chk not in all_active_dates:
            chk = today - timedelta(days=1)
        while chk in all_active_dates:
            current_streak += 1
            chk -= timedelta(days=1)

    # 2. Compute individual components
    ats_comp = calculate_ats_component(all_ats)
    has_attempts = any(a.status == DSAAttemptStatus.SOLVED for a in attempts)
    dsa_comp = calculate_dsa_component(masteries, topics, has_attempts=has_attempts)
    iv_comp = calculate_interview_component(interviews)
    cons_comp = calculate_consistency_component(sorted_active, current_streak, as_of=today)

    composite, confidence, weights = calculate_composite_readiness(
        ats=ats_comp,
        dsa=dsa_comp,
        interview=iv_comp,
        consistency=cons_comp,
    )

    has_enough_data = confidence >= 0.25 and composite is not None

    # 3. Simulate Levers
    levers_data = simulate_levers(
        current_composite=composite,
        ats=ats_comp,
        dsa=dsa_comp,
        interview=iv_comp,
        consistency=cons_comp,
        masteries=masteries,
        topics=topics,
    )
    levers = [ReadinessLeverResponse(**lev) for lev in levers_data]

    # 4. Lazy snapshot write if last is > 6h old
    snap_stmt = (
        select(ReadinessSnapshot)
        .where(ReadinessSnapshot.user_id == current_user.id)
        .order_by(ReadinessSnapshot.created_at.desc())
        .limit(1)
    )
    last_snap = (await db.execute(snap_stmt)).scalar_one_or_none()

    if composite is not None:
        if not last_snap or (now - last_snap.created_at).total_seconds() > 6 * 3600:
            new_snap = ReadinessSnapshot(
                user_id=current_user.id,
                ats=ats_comp,
                dsa=dsa_comp,
                interview=iv_comp,
                consistency=cons_comp,
                composite=composite,
                confidence=confidence,
                explanation={"weights": weights, "levers": levers_data},
            )
            db.add(new_snap)
            await db.commit()

    # 5. Delta vs snapshot from >= 7 days ago
    past_7d_stmt = (
        select(ReadinessSnapshot)
        .where(
            and_(
                ReadinessSnapshot.user_id == current_user.id,
                ReadinessSnapshot.created_at <= now - timedelta(days=7),
            )
        )
        .order_by(ReadinessSnapshot.created_at.desc())
        .limit(1)
    )
    past_snap = (await db.execute(past_7d_stmt)).scalar_one_or_none()
    delta_7d = None
    if past_snap and composite is not None:
        delta_7d = round(composite - past_snap.composite, 1)

    # 6. Sparkline series for the selected range
    cutoff_date = today - timedelta(days=num_days - 1)
    
    # ATS sparkline
    ats_by_date = defaultdict(list)
    for a in all_ats:
        d = a.created_at.date()
        if d >= cutoff_date:
            ats_by_date[d].append(a.overall)

    ats_sparkline = []
    for i in range(num_days - 1, -1, -1):
        d_val = today - timedelta(days=i)
        scores = ats_by_date.get(d_val, [])
        val = sum(scores) / len(scores) if scores else 0.0
        ats_sparkline.append(SparklinePoint(date=d_val.isoformat(), value=round(val, 1)))

    # DSA sparkline (solved count per day)
    dsa_by_date = defaultdict(int)
    for a in attempts:
        if a.status == DSAAttemptStatus.SOLVED:
            d = a.attempted_at.date()
            if d >= cutoff_date:
                dsa_by_date[d] += 1

    dsa_sparkline = []
    for i in range(num_days - 1, -1, -1):
        d_val = today - timedelta(days=i)
        dsa_sparkline.append(SparklinePoint(date=d_val.isoformat(), value=float(dsa_by_date.get(d_val, 0))))

    # Mock interview sparkline
    mock_by_date = defaultdict(list)
    for iv in interviews:
        if iv.status == MockInterviewStatus.COMPLETED and iv.final_score is not None:
            d = iv.started_at.date()
            if d >= cutoff_date:
                mock_by_date[d].append(iv.final_score)

    mock_sparkline = []
    for i in range(num_days - 1, -1, -1):
        d_val = today - timedelta(days=i)
        scores = mock_by_date.get(d_val, [])
        val = sum(scores) / len(scores) if scores else 0.0
        mock_sparkline.append(SparklinePoint(date=d_val.isoformat(), value=round(val, 1)))

    # Averages
    ats_avg = round(sum(a.overall for a in all_ats) / len(all_ats), 1) if all_ats else None
    completed_ivs = [iv for iv in interviews if iv.status == MockInterviewStatus.COMPLETED and iv.final_score is not None]
    mock_avg = round(sum(iv.final_score for iv in completed_ivs) / len(completed_ivs), 1) if completed_ivs else None

    # Topics covered count
    topics_covered = sum(1 for m in masteries.values() if m >= 0.1)

    # 7. Focus task
    focus_task = await determine_daily_focus_task(current_user.id, db)

    # 8. Recent activity feed
    act_stmt = (
        select(ActivityEvent)
        .where(ActivityEvent.user_id == current_user.id)
        .order_by(ActivityEvent.created_at.desc())
        .limit(10)
    )
    activities = (await db.execute(act_stmt)).scalars().all()
    recent_activity = [
        {
            "id": str(e.id),
            "type": e.type,
            "title": e.title,
            "detail": e.detail,
            "created_at": e.created_at.isoformat(),
        }
        for e in activities
    ]

    # 9. Onboarding checklist
    resume_count = (await db.execute(select(func.count(Resume.id)).where(Resume.user_id == current_user.id))).scalar() or 0
    onboarding = {
        "has_uploaded_resume": resume_count > 0,
        "has_logged_3_problems": len(attempts) >= 3,
        "has_taken_mock": len(completed_ivs) >= 1,
    }

    first_name = current_user.name.split()[0] if current_user.name else "Candidate"

    return DashboardSummaryResponse(
        user_name=first_name,
        composite=composite,
        confidence=confidence,
        has_enough_data=has_enough_data,
        delta_7d=delta_7d,
        components={
            "ats": ats_comp,
            "dsa": dsa_comp,
            "interview": iv_comp,
            "consistency": cons_comp,
        },
        weights=weights,
        levers=levers,
        ats_sparkline=ats_sparkline,
        dsa_sparkline=dsa_sparkline,
        mock_sparkline=mock_sparkline,
        ats_average=ats_avg,
        dsa_topics_covered=topics_covered,
        dsa_total_topics=total_topics_count,
        current_streak=current_streak,
        mock_average=mock_avg,
        daily_focus_task=focus_task,
        recent_activity=recent_activity,
        onboarding_checklist=onboarding,
    )

@router.get("/readiness/history", response_model=PaginatedResponse[ReadinessHistoryResponse])
async def get_readiness_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ReadinessSnapshot)
        .where(ReadinessSnapshot.user_id == current_user.id)
        .order_by(ReadinessSnapshot.created_at.asc())
        .limit(60)
    )
    snaps = (await db.execute(stmt)).scalars().all()
    items = [ReadinessHistoryResponse.model_validate(s) for s in snaps]
    return PaginatedResponse(items=items, total=len(items), limit=len(items), offset=0)
