from datetime import datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel


class VitalCreateRequest(BaseModel):
    systolic: int | None = None
    diastolic: int | None = None
    blood_sugar: float | None = None
    weight: float | None = None
    heart_rate: int | None = None
    notes: str | None = None


class VitalResponse(BaseSerializerModel):
    id: int
    patient_id: int
    systolic: int | None
    diastolic: int | None
    blood_sugar: float | None
    weight: float | None
    heart_rate: int | None
    notes: str | None
    alert_message: str | None
    recorded_at: datetime
