from datetime import date, timedelta

import pytest

from app.services.readiness.calculator import (
    BASE_WEIGHTS,
    calculate_composite_readiness,
    calculate_consistency_component,
    simulate_levers,
)


def test_missing_components_renormalisation():
    """Missing components must be excluded and remaining weights renormalised to 1.0."""
    # Case 1: Only consistency (confidence = 0.10)
    comp, conf, weights = calculate_composite_readiness(
        ats=None, dsa=None, interview=None, consistency=40.0
    )
    assert conf == 0.10
    assert weights["consistency"] == 1.0
    assert comp == 40.0

    # Case 2: DSA and Consistency present (confidence = 0.35 + 0.10 = 0.45)
    comp2, conf2, weights2 = calculate_composite_readiness(
        ats=None, dsa=80.0, interview=None, consistency=50.0
    )
    assert conf2 == 0.45
    expected_dsa_weight = 0.35 / 0.45
    expected_cons_weight = 0.10 / 0.45
    assert pytest.approx(weights2["dsa"], rel=1e-3) == expected_dsa_weight
    assert pytest.approx(weights2["consistency"], rel=1e-3) == expected_cons_weight
    expected_comp2 = expected_dsa_weight * 80.0 + expected_cons_weight * 50.0
    assert pytest.approx(comp2, rel=1e-2) == expected_comp2

    # Case 3: All 4 components present (confidence = 1.0)
    comp3, conf3, weights3 = calculate_composite_readiness(
        ats=70.0, dsa=80.0, interview=90.0, consistency=60.0
    )
    assert conf3 == 1.0
    assert weights3 == BASE_WEIGHTS
    expected_comp3 = 0.25 * 70.0 + 0.35 * 80.0 + 0.30 * 90.0 + 0.10 * 60.0
    assert pytest.approx(comp3, rel=1e-2) == expected_comp3

def test_consistency_formula():
    """Consistency must evaluate 60% 28-day active days and 40% 14-day streak."""
    today = date.today()
    
    # Perfect consistency: 28 active days and 14 streak
    perfect_dates = [today - timedelta(days=i) for i in range(28)]
    score_perfect = calculate_consistency_component(perfect_dates, 14, as_of=today)
    assert score_perfect == 100.0

    # Zero consistency
    score_zero = calculate_consistency_component([], 0, as_of=today)
    assert score_zero == 0.0

    # 14 active days (50% of 60 = 30) + 7 streak (50% of 40 = 20) = 50.0
    half_dates = [today - timedelta(days=i * 2) for i in range(14)]
    score_half = calculate_consistency_component(half_dates, 7, as_of=today)
    assert pytest.approx(score_half, rel=1e-1) == 50.0

def test_levers_simulation_ordering():
    """Levers must produce positive gains and be sorted descending by gain."""
    levers = simulate_levers(
        current_composite=55.0,
        ats=60.0,
        dsa=50.0,
        interview=60.0,
        consistency=40.0,
        masteries={},
        topics=[],
    )
    assert len(levers) == 3
    for lev in levers:
        assert lev["gain"] > 0
        assert "action_url" in lev
        assert "title" in lev
    
    assert levers[0]["gain"] >= levers[1]["gain"] >= levers[2]["gain"]
