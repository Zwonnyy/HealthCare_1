from datetime import UTC, datetime

from app.models.notifications import Notification, NotificationType


class NotificationRepository:
    def __init__(self):
        self._model = Notification

    async def create_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        body: str,
    ) -> Notification:
        return await self._model.create(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
        )

    async def get_notification(self, notification_id: int) -> Notification | None:
        return await self._model.get_or_none(id=notification_id)

    async def get_user_notifications(self, user_id: int, offset: int = 0, limit: int = 20) -> list[Notification]:
        return await self._model.filter(user_id=user_id).order_by("-created_at").offset(offset).limit(limit)

    async def count_user_notifications(self, user_id: int) -> int:
        return await self._model.filter(user_id=user_id).count()

    async def count_unread(self, user_id: int) -> int:
        return await self._model.filter(user_id=user_id, is_read=False).count()

    async def mark_as_read(self, notification_id: int) -> None:
        await self._model.filter(id=notification_id).update(
            is_read=True,
            read_at=datetime.now(tz=UTC),
        )

    async def mark_all_as_read(self, user_id: int) -> None:
        await self._model.filter(user_id=user_id, is_read=False).update(
            is_read=True,
            read_at=datetime.now(tz=UTC),
        )
