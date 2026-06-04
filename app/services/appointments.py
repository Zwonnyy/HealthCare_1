from fastapi import HTTPException
from starlette import status

from app.dtos.appointments import AppointmentCreateRequest, AppointmentUpdateRequest
from app.models.appointments import Appointment, AppointmentStatus
from app.models.notifications import NotificationType
from app.models.users import User, UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.notification_repository import NotificationRepository


class AppointmentService:
    def __init__(self):
        self.repo = AppointmentRepository()
        self.notif_repo = NotificationRepository()

    async def create_appointment(self, patient: User, data: AppointmentCreateRequest) -> Appointment:
        appt = await self.repo.create(
            patient_id=patient.id,
            doctor_id=data.doctor_id,
            requested_at=data.requested_at,
            patient_notes=data.patient_notes,
        )
        await self.notif_repo.create_notification(
            user_id=data.doctor_id,
            notification_type=NotificationType.APPOINTMENT_REQUESTED,
            title="새 예약 요청",
            body=f"{patient.name}님이 {data.requested_at.strftime('%Y-%m-%d %H:%M')} 예약을 요청했어요.",
        )
        return appt

    async def get_appointments(self, user: User, offset: int, limit: int) -> tuple[list[Appointment], int]:
        if user.role == UserRole.PATIENT:
            items = await self.repo.list_for_patient(user.id, offset=offset, limit=limit)
            total = await self.repo.count_for_patient(user.id)
        else:
            items = await self.repo.list_for_doctor(user.id, offset=offset, limit=limit)
            total = await self.repo.count_for_doctor(user.id)
        return items, total

    async def update_appointment(
        self, doctor: User, appointment_id: int, data: AppointmentUpdateRequest
    ) -> Appointment:
        appt = await self.repo.get(appointment_id)
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다.")
        if appt.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        await self.repo.update_status(appointment_id, data.status, data.doctor_notes)

        if data.status == AppointmentStatus.CONFIRMED:
            await self.notif_repo.create_notification(
                user_id=appt.patient_id,
                notification_type=NotificationType.APPOINTMENT_CONFIRMED,
                title="예약이 확정됐어요",
                body=f"{appt.requested_at.strftime('%Y-%m-%d %H:%M')} 예약이 확정됐어요.",
            )
        elif data.status == AppointmentStatus.CANCELLED:
            await self.notif_repo.create_notification(
                user_id=appt.patient_id,
                notification_type=NotificationType.APPOINTMENT_CONFIRMED,
                title="예약이 취소됐어요",
                body=f"{appt.requested_at.strftime('%Y-%m-%d %H:%M')} 예약이 취소됐습니다.",
            )

        appt.status = data.status
        if data.doctor_notes is not None:
            appt.doctor_notes = data.doctor_notes
        return appt

    async def cancel_appointment(self, patient: User, appointment_id: int) -> None:
        appt = await self.repo.get(appointment_id)
        if not appt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다.")
        if appt.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if appt.status not in (AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="취소할 수 없는 상태입니다.")
        await self.repo.update_status(appointment_id, AppointmentStatus.CANCELLED)
