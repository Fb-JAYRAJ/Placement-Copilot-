import uuid
from datetime import date, timedelta
from typing import Any

from app.models.models import (
    ATSAnalysis,
    DSATopic,
    MockInterview,
    MockInterviewStatus,
)

BASE_WEIGHTS = {
    "ats": 0.25,
    "dsa": 0.35,
    "interview": 0.30,
    "consistency": 0.10,
}

def calculate_ats_component(analyses: list[ATSAnalysis]) -> float | None:
    """
    ats = recency-weighted mean (0.5/0.3/0.2) of the last three analyses.
    """
    if not analyses:
        return None

    # Take up to 3 most recent
    recent = analyses[:3]
    if len(recent) == 1:
        weights = [1.0]
    elif len(recent) == 2:
        weights = [0.5 / 0.8, 0.3 / 0.8]  # Renormalized 0.5 and 0.3
    else:
        weights = [0.5, 0.3, 0.2]

    weighted_sum = sum(w * a.overall for w, a in zip(weights, recent))
    return round(float(weighted_sum), 2)

def calculate_dsa_component(
    masteries: dict[uuid.UUID, float],
    topics: list[DSATopic],
    has_attempts: bool,
) -> float | None:
    """
    dsa = 0.7·importance-weighted mean mastery + 0.3·breadth (share of topics with mastery ≥ 0.3).
    """
    if not has_attempts or not topics:
        return None

    total_importance = sum(t.importance for t in topics)
    if total_importance == 0:
        return 0.0

    weighted_mastery_sum = sum(
        t.importance * masteries.get(t.id, 0.0) for t in topics
    )
    weighted_mean_mastery = (weighted_mastery_sum / total_importance) * 100.0  # 0 to 100

    # Breadth: share of topics with mastery >= 0.3
    broad_count = sum(1 for t in topics if masteries.get(t.id, 0.0) >= 0.3)
    breadth = (broad_count / len(topics)) * 100.0  # 0 to 100

    dsa_score = 0.7 * weighted_mean_mastery + 0.3 * breadth
    return round(max(0.0, min(100.0, dsa_score)), 2)

def calculate_interview_component(interviews: list[MockInterview]) -> float | None:
    """
    interview = 0.7·EWMA(α=0.5) of the last five sessions’ score×10 + 0.3·((θ−1)/4·100).
    """
    completed = [
        iv for iv in interviews
        if iv.status == MockInterviewStatus.COMPLETED and iv.final_score is not None
    ]
    if not completed:
        return None

    # Take up to last 5 completed sessions (chronological order for EWMA)
    recent_5 = list(reversed(completed[:5]))
    
    alpha = 0.5
    # EWMA calculation: S_0 = Y_0, S_t = alpha * Y_t + (1 - alpha) * S_{t-1}
    # Score is 0-10, score * 10 -> 0-100
    ewma = recent_5[0].final_score * 10.0
    for iv in recent_5[1:]:
        val = iv.final_score * 10.0
        ewma = alpha * val + (1.0 - alpha) * ewma

    # Latest theta ability
    latest_theta = completed[0].ability
    theta_component = max(0.0, min(100.0, ((latest_theta - 1.0) / 4.0) * 100.0))

    score = 0.7 * ewma + 0.3 * theta_component
    return round(max(0.0, min(100.0, score)), 2)

def calculate_consistency_component(
    active_dates: list[date],
    current_streak: int,
    as_of: date | None = None,
) -> float:
    """
    consistency = 100·(0.6·active_days_28/28 + 0.4·min(1, streak/14)).
    """
    if as_of is None:
        as_of = date.today()

    cutoff_28 = as_of - timedelta(days=28)
    recent_dates = set(d for d in active_dates if d >= cutoff_28)
    active_days_28 = len(recent_dates)

    term1 = 0.6 * (min(28, active_days_28) / 28.0)
    term2 = 0.4 * min(1.0, current_streak / 14.0)
    
    score = 100.0 * (term1 + term2)
    return round(max(0.0, min(100.0, score)), 2)

def calculate_composite_readiness(
    ats: float | None,
    dsa: float | None,
    interview: float | None,
    consistency: float,
) -> tuple[float | None, float, dict[str, float]]:
    """
    composite = 0.25·ats + 0.35·dsa + 0.30·interview + 0.10·consistency.
    Components with no data are excluded and weights renormalised;
    confidence = share of weight with data.
    """
    components = {
        "ats": ats,
        "dsa": dsa,
        "interview": interview,
        "consistency": consistency,
    }

    present_weights = {
        k: BASE_WEIGHTS[k]
        for k, v in components.items()
        if v is not None
    }

    confidence = round(sum(present_weights.values()), 3)
    if confidence == 0:
        return None, 0.0, {}

    # Renormalise weights
    renormalized_weights = {
        k: w / confidence
        for k, w in present_weights.items()
    }

    composite = sum(renormalized_weights[k] * components[k] for k in present_weights)
    return round(max(0.0, min(100.0, composite)), 2), confidence, renormalized_weights

def simulate_levers(
    current_composite: float | None,
    ats: float | None,
    dsa: float | None,
    interview: float | None,
    consistency: float,
    masteries: dict[uuid.UUID, float],
    topics: list[DSATopic],
) -> list[dict[str, Any]]:
    """
    levers: simulate +1 solved medium problem, +10 ATS points, one more mock session;
    return top 3 with estimated composite gain.
    """
    curr = current_composite if current_composite is not None else 0.0
    levers = []

    # 1. Simulate +10 ATS points
    sim_ats = min(100.0, (ats or 60.0) + 10.0)
    sim_comp_ats, _, _ = calculate_composite_readiness(
        ats=sim_ats, dsa=dsa, interview=interview, consistency=consistency
    )
    gain_ats = round(max(0.5, (sim_comp_ats or curr) - curr), 1)
    levers.append({
        "id": "lever_ats_boost",
        "title": "Optimize Resume Alignment (+10 ATS pts)",
        "description": "Incorporate missing high-importance job description keywords into project bullet points.",
        "gain": gain_ats,
        "type": "resume",
        "action_url": "/resume",
    })

    # 2. Simulate +1 Solved Medium DSA Problem in lowest mastery topic
    sim_masteries = masteries.copy()
    if topics:
        weakest_topic = min(topics, key=lambda t: sim_masteries.get(t.id, 0.0))
        curr_m = sim_masteries.get(weakest_topic.id, 0.0)
        # Medium problem solved with confidence 4 gives w * c = 2.0 * 1.0 = 2.0 evidence
        # mastery = 1 - exp(-(S + 2)/target)
        # approximate bump:
        sim_masteries[weakest_topic.id] = min(1.0, curr_m + 0.15)
        sim_dsa = calculate_dsa_component(sim_masteries, topics, has_attempts=True)
    else:
        sim_dsa = (dsa or 50.0) + 5.0

    sim_comp_dsa, _, _ = calculate_composite_readiness(
        ats=ats, dsa=sim_dsa, interview=interview, consistency=consistency
    )
    gain_dsa = round(max(0.5, (sim_comp_dsa or curr) - curr), 1)
    levers.append({
        "id": "lever_dsa_solve",
        "title": "Solve 1 Medium DSA Problem",
        "description": "Strengthen your weakest topic mastery to expand coverage breadth.",
        "gain": gain_dsa,
        "type": "dsa",
        "action_url": "/dsa",
    })

    # 3. Simulate Complete 1 More Mock Session
    sim_interview = min(100.0, (interview or 65.0) + 8.0)
    sim_comp_iv, _, _ = calculate_composite_readiness(
        ats=ats, dsa=dsa, interview=sim_interview, consistency=consistency
    )
    gain_iv = round(max(0.5, (sim_comp_iv or curr) - curr), 1)
    levers.append({
        "id": "lever_mock_session",
        "title": "Complete 1 Adaptive Mock Session",
        "description": "Benchmark your problem-solving depth and elevate your IRT ability score.",
        "gain": gain_iv,
        "type": "interview",
        "action_url": "/interview",
    })

    # Sort descending by gain
    levers.sort(key=lambda x: x["gain"], reverse=True)
    return levers[:3]
