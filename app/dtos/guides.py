from datetime import datetime

from app.dtos.base import BaseSerializerModel
from app.models.guides import GuideStatus


class GuideResponse(BaseSerializerModel):
    id: int
    record_id: int
    medication_guide: str | None
    lifestyle_guide: str | None
    status: GuideStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime