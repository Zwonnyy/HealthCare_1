import logging
from datetime import UTC, date, datetime

from fastapi import HTTPException
from starlette import status

from app.dtos.medication_reminders import ReminderCreateRequest, ReminderUpdateRequest
from app.models.medication_reminders import MedicationReminder
from app.models.users import User

logger = logging.getLogger(__name__)


class MedicationReminderService:
    async def create(self, patient: User, data: ReminderCreateRequest) -> MedicationReminder:
        return await MedicationReminder.create(
            patient_id=patient.id,
            name=data.name,
            reminder_time=data.reminder_time,
        )

    async def list_reminders(self, patient: User) -> list[MedicationReminder]:
        return await MedicationReminder.filter(patient_id=patient.id).order_by("reminder_time")

    async def update(self, patient: User, reminder_id: int, data: ReminderUpdateRequest) -> MedicationReminder:
        reminder = await MedicationReminder.get_or_none(id=reminder_id, patient_id=patient.id)
        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
        update_data = data.model_dump(exclude_none=True)
        if update_data:
            await MedicationReminder.filter(id=reminder_id).update(**update_data)
            reminder = await MedicationReminder.get(id=reminder_id)
        return reminder

    async def delete(self, patient: User, reminder_id: int) -> None:
        reminder = await MedicationReminder.get_or_none(id=reminder_id, patient_id=patient.id)
        if not reminder:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="알림을 찾을 수 없습니다.")
        await reminder.delete()


async def send_due_reminders() -> int:
    """매 분 Celery Beat에서 호출: 현재 시각과 reminder_time이 일치하면 인앱 알림 발송."""
    from app.models.notifications import NotificationType
    from app.repositories.notification_repository import NotificationRepository

    now = datetime.now(tz=UTC).astimezone()
    current_time = now.strftime("%H:%M")
    today = date.today()

    reminders = await MedicationReminder.filter(
        enabled=True,
        reminder_time=current_time,
    ).exclude(last_notified_date=today)

    notif_repo = NotificationRepository()
    count = 0
    for reminder in reminders:
        try:
            await notif_repo.create_notification(
                user_id=reminder.patient_id,
                notification_type=NotificationType.MEDICATION_REMINDER,
                title="복약 알림",
                body=f"'{reminder.name}' 복약 시간입니다. ({reminder.reminder_time})",
            )
            await MedicationReminder.filter(id=reminder.id).update(last_notified_date=today)
            count += 1
        except Exception as e:
            logger.warning("Reminder notification failed for id=%d: %s", reminder.id, e)
    return count
