from datetime import datetime

from app.dtos.base import BaseSerializerModel
from app.models.notifications import NotificationType


class NotificationResponse(BaseSerializerModel):
    id: int
    user_id: int
    notification_type: NotificationType
    title: str
    body: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime


class UnreadCountResponse(BaseSerializerModel):
    count: int
