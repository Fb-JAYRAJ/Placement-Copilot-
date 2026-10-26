from datetime import UTC, datetime, timedelta


def calculate_sm2(
    quality: int,
    previous_repetitions: int = 0,
    previous_ease: float = 2.5,
    previous_interval: int = 1,
    review_time: datetime = None,
) -> tuple[int, float, int, datetime]:
    """
    SuperMemo SM-2 algorithm for spaced repetition.
    quality: 0 to 5 (0-2 fail, 3-5 pass)
    Returns: (repetitions, ease_factor, interval_days, next_review_at)
    """
    if review_time is None:
        review_time = datetime.now(UTC)
    
    # Bound quality between 0 and 5
    q = max(0, min(5, quality))
    
    # Calculate new ease factor
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ease = previous_ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ease = max(1.3, new_ease)
    
    if q >= 3:
        if previous_repetitions == 0:
            new_interval = 1
        elif previous_repetitions == 1:
            new_interval = 6
        else:
            new_interval = round(previous_interval * new_ease)
        new_repetitions = previous_repetitions + 1
    else:
        new_repetitions = 0
        new_interval = 1
    
    next_review_at = review_time + timedelta(days=new_interval)
    return new_repetitions, round(new_ease, 4), new_interval, next_review_at
