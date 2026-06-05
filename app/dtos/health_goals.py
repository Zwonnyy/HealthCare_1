from datetime import date, datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel
from app.models.health_goals import GoalType


class HealthGoalHistoryResponse(BaseSerializerModel):
    id: int
    recorded_value: float
    recorded_at: datetime


class HealthGoalCreateRequest(BaseModel):
    goal_type: GoalType
    title: str
    target_value: float
    unit: str
    deadline: date | None = None


class HealthGoalRecommendationResponse(BaseModel):
    goal_type: GoalType
    title: str
    target_value: float
    unit: str
    deadline: date | None
    reason: str


class HealthGoalUpdateRequest(BaseModel):
    current_value: float | None = None
    achieved: bool | None = None


class HealthGoalResponse(BaseSerializerModel):
    id: int
    patient_id: int
    goal_type: GoalType
    title: str
    target_value: float
    current_value: float | None
    unit: str
    deadline: date | None
    achieved: bool
    created_at: datetime
    updated_at: datetime

    @property
    def progress_pct(self) -> float | None:
        if self.current_value is None or self.target_value == 0:
            return None
        return min(round(self.current_value / self.target_value * 100, 1), 100.0)
