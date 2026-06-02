from datetime import datetime

from app.dtos.base import BaseSerializerModel
from app.models.health_reports import ReportStatus


class HealthReportResponse(BaseSerializerModel):
    id: int
    patient_id: int
    year: int
    month: int
    report_text: str | None
    status: ReportStatus
    error_message: str | None
    created_at: datetime
