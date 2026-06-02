from datetime import datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel
from app.models.appointments import AppointmentStatus


class AppointmentCreateRequest(BaseModel):
    doctor_id: int
    requested_at: datetime
    patient_notes: str | None = None


class AppointmentUpdateRequest(BaseModel):
    status: AppointmentStatus
    doctor_notes: str | None = None


class AppointmentResponse(BaseSerializerModel):
    id: int
    patient_id: int
    doctor_id: int
    requested_at: datetime
    status: AppointmentStatus
    patient_notes: str | None
    doctor_notes: str | None
    created_at: datetime
    updated_at: datetime
