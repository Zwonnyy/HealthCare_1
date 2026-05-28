from datetime import datetime

from app.dtos.base import BaseSerializerModel


class MessageSendRequest(BaseSerializerModel):
    receiver_id: int
    record_id: int | None = None
    content: str


class MessageResponse(BaseSerializerModel):
    id: int
    sender_id: int
    receiver_id: int
    record_id: int | None
    content: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime