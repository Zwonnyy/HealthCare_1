from fastapi import HTTPException
from starlette import status
from tortoise.transactions import in_transaction

from app.dtos.records import ActionPlanItem, ActionPlanResponse, MedicalRecordCreateRequest, MedicalRecordUpdateRequest
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

    async def get_records(
        self, user: User, offset: int = 0, limit: int = 20, q: str | None = None
    ) -> tuple[list[MedicalRecord], int]:
        if q:
            if user.role == UserRole.DOCTOR:
                items = await self.record_repo.search_doctor_records(user.id, q, offset=offset, limit=limit)
                total = await self.record_repo.count_search_doctor_records(user.id, q)
            else:
                items = await self.record_repo.search_patient_records(user.id, q, offset=offset, limit=limit)
                total = await self.record_repo.count_search_patient_records(user.id, q)
        else:
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

    async def update_record(self, doctor: User, record_id: int, data: MedicalRecordUpdateRequest) -> MedicalRecord:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if record.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return await self.record_repo.update_record(record, data.model_dump(exclude_none=True))

    async def action_plan(self, user: User, record_id: int) -> ActionPlanResponse:
        record = await self.get_record(user=user, record_id=record_id)
        prescriptions = await record.prescriptions.all()
        items = [
            ActionPlanItem(
                category="증상 관찰",
                title="오늘 증상 변화 기록",
                detail=f"진료 시 호소한 증상({record.symptoms})의 강도와 변화를 건강일지에 남기세요.",
                due_label="오늘",
                priority="높음",
            ),
            ActionPlanItem(
                category="재확인",
                title="악화 신호 확인",
                detail="흉통, 호흡곤란, 의식 변화, 갑작스러운 악화가 있으면 즉시 의료진에게 연락하거나 응급 진료를 받으세요.",
                due_label="상시",
                priority="높음",
            ),
        ]
        for prescription in prescriptions:
            items.append(
                ActionPlanItem(
                    category="복약",
                    title=f"{prescription.medication_name} 복용 체크",
                    detail=(
                        f"{prescription.dosage}, {prescription.frequency}, {prescription.duration_days}일간 복용"
                        f"{f' · {prescription.instructions}' if prescription.instructions else ''}"
                    ),
                    due_label="매일",
                    priority="높음",
                )
            )
        if record.notes:
            items.append(
                ActionPlanItem(
                    category="의사 지시",
                    title="진료 메모 확인",
                    detail=record.notes,
                    due_label="오늘",
                    priority="중간",
                )
            )
        items.append(
            ActionPlanItem(
                category="추적 관리",
                title="다음 진료 전 상태 점검",
                detail="처방 종료 전 복약 체크율, 증상 변화, 바이탈 기록을 확인하고 필요하면 예약을 요청하세요.",
                due_label="처방 종료 전",
                priority="중간",
            )
        )
        return ActionPlanResponse(
            record_id=record.id,
            patient_id=record.patient_id,
            title=f"{record.diagnosis} 진료 후 액션 플랜",
            summary="진료 후 복약, 증상 관찰, 위험 신호 확인을 체크리스트로 정리했습니다.",
            items=items,
        )
