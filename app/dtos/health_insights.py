from datetime import datetime

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class RiskSignal(BaseModel):
    label: str
    detail: str
    severity: int = Field(ge=0, le=30)


class HealthRiskResponse(BaseModel):
    risk_level: str
    score: int
    summary: str
    signals: list[RiskSignal]
    recommendations: list[str]


class MedicationAdherenceItem(BaseModel):
    prescription_id: int
    medication_name: str
    expected_days: int
    checked_days: int
    adherence_rate: float


class MedicationAdherenceResponse(BaseModel):
    period_days: int
    overall_rate: float
    summary: str
    items: list[MedicationAdherenceItem]


class PreVisitQuestionnaireCreateRequest(BaseModel):
    symptoms: str
    onset: str | None = None
    severity: int | None = Field(default=None, ge=0, le=10)
    medications: str | None = None
    history: str | None = None
    questions: str | None = None


class PreVisitQuestionnaireResponse(BaseSerializerModel):
    id: int
    appointment_id: int
    patient_id: int
    symptoms: str
    onset: str | None
    severity: int | None
    medications: str | None
    history: str | None
    questions: str | None
    ai_summary: str | None
    created_at: datetime
    updated_at: datetime
