from fastapi import HTTPException
from starlette import status

from app.dtos.messages import MessageSendRequest
from app.models.messages import Message
from app.models.notifications import NotificationType
from app.models.users import User, UserRole
from app.repositories.message_repository import MessageRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.record_repository import RecordRepository
from app.repositories.user_repository import UserRepository


class MessageService:
    def __init__(self):
        self.message_repo = MessageRepository()
        self.record_repo = RecordRepository()
        self.notification_repo = NotificationRepository()
        self.user_repo = UserRepository()

    async def send_message(self, sender: User, data: MessageSendRequest) -> Message:
        receiver = await self.user_repo.get_user(data.receiver_id)
        if not receiver:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="수신자를 찾을 수 없습니다.")
        if receiver.id == sender.id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="자신에게 메시지를 보낼 수 없습니다.")

        # 의사-환자 관계 검증
        if sender.role == UserRole.DOCTOR and receiver.role != UserRole.PATIENT:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="환자에게만 메시지를 보낼 수 있습니다.")
        if sender.role == UserRole.PATIENT and receiver.role != UserRole.DOCTOR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="의사에게만 메시지를 보낼 수 있습니다.")

        if data.record_id:
            record = await self.record_repo.get_record(data.record_id)
            if not record:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
            doctor_id = sender.id if sender.role == UserRole.DOCTOR else receiver.id
            patient_id = sender.id if sender.role == UserRole.PATIENT else receiver.id
            if record.doctor_id != doctor_id or record.patient_id != patient_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="해당 진료 기록에 대한 권한이 없습니다."
                )

        message = await self.message_repo.create_message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            record_id=data.record_id,
            content=data.content,
        )
        await self.notification_repo.create_notification(
            user_id=receiver.id,
            notification_type=NotificationType.MESSAGE_RECEIVED,
            title="새 메시지",
            body=f"{sender.name}님으로부터 메시지가 도착했습니다.",
        )
        return message

    async def get_inbox(self, user: User, offset: int = 0, limit: int = 20) -> tuple[list[Message], int]:
        items = await self.message_repo.get_inbox(user.id, offset=offset, limit=limit)
        total = await self.message_repo.count_inbox(user.id)
        return items, total

    async def get_sent(self, user: User, offset: int = 0, limit: int = 20) -> tuple[list[Message], int]:
        items = await self.message_repo.get_sent(user.id, offset=offset, limit=limit)
        total = await self.message_repo.count_sent(user.id)
        return items, total

    async def get_message(self, user: User, message_id: int) -> Message:
        message = await self.message_repo.get_message(message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="메시지를 찾을 수 없습니다.")
        if message.sender_id != user.id and message.receiver_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if message.receiver_id == user.id and not message.is_read:
            await self.message_repo.mark_as_read(message_id)
            message.is_read = True
        return message

    async def get_record_messages(self, user: User, record_id: int) -> list[Message]:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return await self.message_repo.get_record_messages(record_id)

    async def get_unread_count(self, user: User) -> int:
        return await self.message_repo.count_unread(user.id)
