from datetime import date

from pydantic import BaseModel


class PainTrendPoint(BaseModel):
    date: date
    avg_pain_score: float


class MoodDistribution(BaseModel):
    GREAT: int = 0
    GOOD: int = 0
    NORMAL: int = 0
    BAD: int = 0
    TERRIBLE: int = 0


class HealthLogStats(BaseModel):
    total: int
    avg_pain_score_7d: float | None
    avg_pain_score_30d: float | None
    pain_trend_14d: list[PainTrendPoint]


class PatientDashboardStats(BaseModel):
    total_records: int
    unread_messages: int
    health_log_stats: HealthLogStats
    mood_distribution_30d: MoodDistribution


class DoctorDashboardStats(BaseModel):
    total_patients: int
    total_records: int
    records_last_30d: int
    unread_messages: int
    pending_guides: int
