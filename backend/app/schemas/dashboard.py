import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class SparklinePoint(BaseModel):
    date: str
    value: float

class ReadinessLeverResponse(BaseModel):
    id: str
    title: str
    description: str
    gain: float
    type: str
    action_url: str

class ReadinessHistoryResponse(BaseModel):
    id: uuid.UUID
    composite: float
    confidence: float
    ats: float | None = None
    dsa: float | None = None
    interview: float | None = None
    consistency: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DashboardSummaryResponse(BaseModel):
    user_name: str
    composite: float | None = None
    confidence: float  # share of weight with data 0.0 to 1.0
    has_enough_data: bool
    delta_7d: float | None = None
    components: dict[str, float | None]
    weights: dict[str, float]
    levers: list[ReadinessLeverResponse]
    ats_sparkline: list[SparklinePoint]
    dsa_sparkline: list[SparklinePoint]
    mock_sparkline: list[SparklinePoint]
    ats_average: float | None = None
    dsa_topics_covered: int
    dsa_total_topics: int
    current_streak: int
    mock_average: float | None = None
    daily_focus_task: dict[str, Any]
    recent_activity: list[dict[str, Any]]
    onboarding_checklist: dict[str, bool]
