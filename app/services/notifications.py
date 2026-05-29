from fastapi import HTTPException
from starlette import status

from app.models.notifications import Notification, NotificationType
from app.models.users import User
from app.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self):
        self.repo = NotificationRepository()

    async def get_notifications(self, user: User, offset: int = 0, limit: int = 20) -> tuple[list[Notification], int]:
        items = await self.repo.get_user_notifications(user.id, offset=offset, limit=limit)
        total = await self.repo.count_user_notifications(user.id)
        return items, total

    async def get_unread_count(self, user: User) -> int:
        return await self.repo.count_unread(user.id)

    async def mark_as_read(self, user: User, notification_id: int) -> None:
        notification = await self.repo.get_notification(notification_id)
        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
        if notification.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if not notification.is_read:
            await self.repo.mark_as_read(notification_id)

    async def mark_all_as_read(self, user: User) -> None:
        await self.repo.mark_all_as_read(user.id)

    async def notify(self, user_id: int, notification_type: NotificationType, title: str, body: str) -> None:
        await self.repo.create_notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            body=body,
        )
