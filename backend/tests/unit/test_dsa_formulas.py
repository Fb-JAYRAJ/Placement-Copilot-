import math
from datetime import UTC, datetime, timedelta

from app.models.models import DSAAttemptStatus
from app.services.dsa.mastery import (
    DIFFICULTY_WEIGHTS,
    compute_attempt_evidence,
    compute_mastery_from_evidence,
    compute_topic_priority,
)
from app.services.dsa.sm2 import calculate_sm2


def test_mastery_monotonicity_with_evidence():
    """Mastery must strictly monotonically increase as evidence S increases."""
    s_values = [0.0, 1.0, 3.0, 6.0, 12.0, 24.0, 50.0]
    masteries = [compute_mastery_from_evidence(s) for s in s_values]

    for i in range(len(masteries) - 1):
        assert masteries[i] < masteries[i + 1], f"Monotonicity failed at S={s_values[i]}"

def test_mastery_bounds():
    """Mastery must remain bounded within [0.0, 1.0) for any input."""
    assert compute_mastery_from_evidence(-10.0) == 0.0
    assert compute_mastery_from_evidence(0.0) == 0.0
    huge_mastery = compute_mastery_from_evidence(1000.0)
    assert 0.0 < huge_mastery <= 1.0
    assert huge_mastery >= 0.99999

def test_difficulty_weight_monotonicity():
    """Higher difficulty must yield strictly higher evidence."""
    now = datetime.now(UTC)
    e_easy = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "easy", 3, now, now)
    e_med = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "medium", 3, now, now)
    e_hard = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "hard", 3, now, now)

    assert e_easy < e_med < e_hard
    assert DIFFICULTY_WEIGHTS["easy"] == 1.0
    assert DIFFICULTY_WEIGHTS["medium"] == 2.0
    assert DIFFICULTY_WEIGHTS["hard"] == 3.5

def test_confidence_factor_monotonicity():
    """Higher confidence (1..5) must strictly increase evidence for solved attempts."""
    now = datetime.now(UTC)
    evidences = [
        compute_attempt_evidence(DSAAttemptStatus.SOLVED, "medium", c, now, now)
        for c in range(1, 6)
    ]
    for i in range(len(evidences) - 1):
        assert evidences[i] < evidences[i + 1], f"Confidence monotonicity failed at {i}"

def test_exponential_time_decay():
    """Evidence must decay exponentially with half-life / tau = 45 days."""
    now = datetime.now(UTC)
    past_45_days = now - timedelta(days=45)
    past_90_days = now - timedelta(days=90)

    e_today = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "medium", 3, now, now)
    e_45d = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "medium", 3, past_45_days, now)
    e_90d = compute_attempt_evidence(DSAAttemptStatus.SOLVED, "medium", 3, past_90_days, now)

    # At delta = 45 days (tau), e^(-1) is approx 0.367879
    expected_ratio = math.exp(-1.0)
    actual_ratio = e_45d / e_today
    assert math.isclose(actual_ratio, expected_ratio, rel_tol=1e-3)

    assert e_today > e_45d > e_90d
    assert math.isclose(e_90d / e_today, math.exp(-2.0), rel_tol=1e-3)

def test_failed_attempt_negative_contribution():
    """Failed attempts must contribute negative evidence scaled at 0.5 * weight."""
    now = datetime.now(UTC)
    e_failed = compute_attempt_evidence(DSAAttemptStatus.FAILED, "medium", 1, now, now)
    # Medium weight is 2.0 -> negative contribution is -0.5 * 2.0 = -1.0
    assert e_failed == -1.0

def test_topic_priority_formula():
    """Lower mastery and longer time since practice must increase priority."""
    now = datetime.now(UTC)
    recent = now - timedelta(days=2)
    stale = now - timedelta(days=35)

    p_low_mastery = compute_topic_priority(mastery=0.1, importance=1.0, last_practiced_at=recent, as_of=now)
    p_high_mastery = compute_topic_priority(mastery=0.9, importance=1.0, last_practiced_at=recent, as_of=now)
    assert p_low_mastery > p_high_mastery

    # For same mastery, longer time without practice must increase priority
    p_stale = compute_topic_priority(mastery=0.5, importance=1.0, last_practiced_at=stale, as_of=now)
    p_recent = compute_topic_priority(mastery=0.5, importance=1.0, last_practiced_at=recent, as_of=now)
    assert p_stale > p_recent

def test_sm2_progression_and_bounds():
    """SM-2 must increase interval on pass and reset on failure, with ease >= 1.3."""
    now = datetime.now(UTC)

    # First pass with quality 4
    reps, ease, interval, next_rev = calculate_sm2(quality=4, review_time=now)
    assert reps == 1
    assert interval == 1
    assert ease >= 2.5

    # Second pass
    reps2, ease2, interval2, _ = calculate_sm2(quality=4, previous_repetitions=reps, previous_ease=ease, previous_interval=interval)
    assert reps2 == 2
    assert interval2 == 6

    # Failure resets repetitions and interval to 1
    reps_fail, ease_fail, interval_fail, _ = calculate_sm2(quality=1, previous_repetitions=reps2, previous_ease=ease2, previous_interval=interval2)
    assert reps_fail == 0
    assert interval_fail == 1

    # Ease factor floor at 1.3
    low_ease = 1.35
    for _ in range(5):
        _, low_ease, _, _ = calculate_sm2(quality=0, previous_ease=low_ease)
    assert low_ease == 1.3
