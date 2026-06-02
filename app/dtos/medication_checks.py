from datetime import date, datetime

from pydantic import BaseModel

from app.dtos.base import BaseSerializerModel
from app.dtos.records import PrescriptionResponse


class TodayMedicationItem(BaseModel):
    prescription: PrescriptionResponse
    checked: bool


class MedicationCheckResponse(BaseSerializerModel):
    id: int
    prescription_id: int
    check_date: date
    checked_at: datetime
