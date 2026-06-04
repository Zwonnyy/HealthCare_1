from datetime import datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel
from app.models.symptom_checks import UrgencyLevel


class SymptomCheckRequest(BaseModel):
    symptom_text: str


class SymptomCheckResponse(BaseSerializerModel):
    id: int
    symptom_text: str
    ai_assessment: str | None
    urgency: UrgencyLevel | None
    suggest_appointment: bool
    created_at: datetime
