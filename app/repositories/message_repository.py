from datetime import UTC, datetime

from app.models.messages import Message


class MessageRepository:
    def __init__(self):
        self._model = Message

    async def create_message(
        self,
        sender_id: int,
        receiver_id: int,
        content: str,
        record_id: int | None = None,
    ) -> Message:
        return await self._model.create(
            sender_id=sender_id,
            receiver_id=receiver_id,
            record_id=record_id,
            content=content,
        )

    async def get_message(self, message_id: int) -> Message | None:
        return await self._model.get_or_none(id=message_id)

    async def get_inbox(self, user_id: int) -> list[Message]:
        return await self._model.filter(receiver_id=user_id).order_by("-created_at")

    async def get_sent(self, user_id: int) -> list[Message]:
        return await self._model.filter(sender_id=user_id).order_by("-created_at")

    async def get_record_messages(self, record_id: int) -> list[Message]:
        return await self._model.filter(record_id=record_id).order_by("created_at")

    async def mark_as_read(self, message_id: int) -> None:
        await self._model.filter(id=message_id).update(
            is_read=True,
            read_at=datetime.now(tz=UTC),
        )

    async def count_unread(self, user_id: int) -> int:
        return await self._model.filter(receiver_id=user_id, is_read=False).count()
