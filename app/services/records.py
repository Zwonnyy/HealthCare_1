from fastapi import HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from app.dtos.records import MedicalRecordCreateRequest
from app.models.notifications import NotificationType
from app.models.records import MedicalRecord
from app.models.users import User, UserRole
from app.repositories.notification_repository import NotificationRepository
from app.repositories.record_repository import RecordRepository


class MedicalRecordService:
    def __init__(self):
        self.record_repo = RecordRepository()
        self.notification_repo = NotificationRepository()

    async def create_record(self, doctor: User, data: MedicalRecordCreateRequest) -> MedicalRecord:
        async with in_transaction():
            record = await self.record_repo.create_record(
                patient_id=data.patient_id,
                doctor_id=doctor.id,
                diagnosis=data.diagnosis,
                symptoms=data.symptoms,
                notes=data.notes,
                visited_at=data.visited_at,
            )
            for p in data.prescriptions:
                await self.record_repo.create_prescription(
                    record_id=record.id,
                    medication_name=p.medication_name,
                    dosage=p.dosage,
                    frequency=p.frequency,
                    duration_days=p.duration_days,
                    instructions=p.instructions,
                )
        await self.notification_repo.create_notification(
            user_id=data.patient_id,
            notification_type=NotificationType.RECORD_CREATED,
            title="새 진료 기록",
            body=f"'{data.diagnosis}' 진료 기록이 등록되었습니다.",
        )
        return record

    async def get_records(self, user: User, offset: int = 0, limit: int = 20) -> tuple[list[MedicalRecord], int]:
        if user.role == UserRole.DOCTOR:
            items = await self.record_repo.get_doctor_records(user.id, offset=offset, limit=limit)
            total = await self.record_repo.count_doctor_records(user.id)
        else:
            items = await self.record_repo.get_patient_records(user.id, offset=offset, limit=limit)
            total = await self.record_repo.count_patient_records(user.id)
        return items, total

    async def get_record(self, user: User, record_id: int) -> MedicalRecord:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return record
