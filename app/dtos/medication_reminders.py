from datetime import datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel


class ReminderCreateRequest(BaseModel):
    name: str
    reminder_time: str  # HH:MM


class ReminderUpdateRequest(BaseModel):
    enabled: bool | None = None
    reminder_time: str | None = None
    name: str | None = None


class ReminderResponse(BaseSerializerModel):
    id: int
    patient_id: int
    name: str
    reminder_time: str
    enabled: bool
    created_at: datetime
