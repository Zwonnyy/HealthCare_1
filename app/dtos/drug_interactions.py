from datetime import datetime

from app.dtos.base import BaseSerializerModel
from app.models.drug_interactions import InteractionStatus


class DrugInteractionResponse(BaseSerializerModel):
    id: int
    record_id: int
    status: InteractionStatus
    result_text: str | None
    has_warning: bool
    error_message: str | None
    created_at: datetime
