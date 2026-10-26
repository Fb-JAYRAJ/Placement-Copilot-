import uuid
from collections import defaultdict
from datetime import date, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import DSAAttempt, DSAAttemptStatus


async def compute_dsa_stats(user_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
    # Fetch all attempts for user
    stmt = (
        select(DSAAttempt)
        .where(DSAAttempt.user_id == user_id)
        .order_by(DSAAttempt.attempted_at.asc())
    )
    attempts = (await db.execute(stmt)).scalars().all()

    today = date.today()
    total_attempts = len(attempts)
    solved_attempts = [a for a in attempts if a.status == DSAAttemptStatus.SOLVED]
    total_solved = len(solved_attempts)

    # By difficulty
    by_diff = {"easy": 0, "medium": 0, "hard": 0}
    for a in solved_attempts:
        d = a.difficulty.lower()
        if d in by_diff:
            by_diff[d] += 1

    # Topics covered (distinct topics where user has solved >= 1 problem)
    topics_covered = len(set(a.topic_id for a in solved_attempts))

    # Solved per day map
    solved_by_date = defaultdict(int)
    for a in solved_attempts:
        d = a.attempted_at.date()
        solved_by_date[d] += 1

    # Daily solved series for past 7 days
    solved_7d = []
    for i in range(6, -1, -1):
        day_val = today - timedelta(days=i)
        solved_7d.append({
            "date": day_val.isoformat(),
            "count": solved_by_date.get(day_val, 0),
        })

    # Daily solved series for past 30 days
    solved_30d = []
    for i in range(29, -1, -1):
        day_val = today - timedelta(days=i)
        solved_30d.append({
            "date": day_val.isoformat(),
            "count": solved_by_date.get(day_val, 0),
        })

    # Streaks calculation
    active_dates = sorted(set(a.attempted_at.date() for a in attempts))
    current_streak = 0
    best_streak = 0

    if active_dates:
        # Check current streak
        check_date = today
        if check_date not in active_dates:
            check_date = today - timedelta(days=1)
        
        while check_date in active_dates:
            current_streak += 1
            check_date -= timedelta(days=1)

        # Compute best streak
        temp_streak = 1
        for idx in range(1, len(active_dates)):
            if active_dates[idx] == active_dates[idx - 1] + timedelta(days=1):
                temp_streak += 1
            else:
                best_streak = max(best_streak, temp_streak)
                temp_streak = 1
        best_streak = max(best_streak, temp_streak, current_streak)

    return {
        "total_attempts": total_attempts,
        "total_solved": total_solved,
        "solved_by_difficulty": by_diff,
        "topics_covered": topics_covered,
        "current_streak": current_streak,
        "best_streak": best_streak,
        "solved_7d": solved_7d,
        "solved_30d": solved_30d,
    }
