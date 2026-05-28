from datetime import date, datetime

from pydantic import Field

from app.dtos.base import BaseSerializerModel
from app.models.health_logs import AnalysisStatus, Mood


class HealthLogCreateRequest(BaseSerializerModel):
    record_id: int | None = None
    log_date: date
    pain_score: int = Field(ge=0, le=10)
    mood: Mood
    symptoms_text: str
    notes: str | None = None


class HealthLogResponse(BaseSerializerModel):
    id: int
    patient_id: int
    record_id: int | None
    log_date: date
    pain_score: int
    mood: Mood
    symptoms_text: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class HealthLogAnalysisRequest(BaseSerializerModel):
    record_id: int | None = None


class HealthLogAnalysisResponse(BaseSerializerModel):
    id: int
    patient_id: int
    record_id: int | None
    analysis_text: str | None
    status: AnalysisStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime