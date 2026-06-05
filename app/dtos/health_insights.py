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


class PatientRiskQueueItem(BaseModel):
    patient_id: int
    patient_name: str
    risk_level: str
    score: int
    summary: str
    signals: list[RiskSignal]
    last_activity_at: datetime | None


class PatientRiskQueueResponse(BaseModel):
    period_days: int
    total: int
    high_count: int
    caution_count: int
    items: list[PatientRiskQueueItem]


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


class MedicationPatternDay(BaseModel):
    weekday: str
    expected_count: int
    checked_count: int
    missed_count: int
    adherence_rate: float


class MedicationPatternResponse(BaseModel):
    period_days: int
    current_missed_streak: int
    weakest_weekdays: list[MedicationPatternDay]
    summary: str
    suggestions: list[str]


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


class PatientTimelineItem(BaseModel):
    id: int
    type: str
    title: str
    summary: str
    occurred_at: datetime
    metadata: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class PatientTimelineResponse(BaseModel):
    patient_id: int
    patient_name: str
    period_days: int
    items: list[PatientTimelineItem]


class ClinicalNoteDraftResponse(BaseModel):
    pre_visit_id: int
    appointment_id: int
    patient_id: int
    diagnosis_hint: str
    symptoms: str
    soap_note: str
    follow_up_questions: list[str]
