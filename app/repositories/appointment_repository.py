from app.models.appointments import Appointment, AppointmentStatus


class AppointmentRepository:
    def __init__(self):
        self._model = Appointment

    async def create(self, patient_id: int, doctor_id: int, requested_at, patient_notes: str | None) -> Appointment:
        return await self._model.create(
            patient_id=patient_id,
            doctor_id=doctor_id,
            requested_at=requested_at,
            patient_notes=patient_notes,
        )

    async def get(self, appointment_id: int) -> Appointment | None:
        return await self._model.get_or_none(id=appointment_id)

    async def list_for_patient(self, patient_id: int, offset: int = 0, limit: int = 20) -> list[Appointment]:
        return await self._model.filter(patient_id=patient_id).order_by("-requested_at").offset(offset).limit(limit)

    async def count_for_patient(self, patient_id: int) -> int:
        return await self._model.filter(patient_id=patient_id).count()

    async def list_for_doctor(self, doctor_id: int, offset: int = 0, limit: int = 20) -> list[Appointment]:
        return await self._model.filter(doctor_id=doctor_id).order_by("-requested_at").offset(offset).limit(limit)

    async def count_for_doctor(self, doctor_id: int) -> int:
        return await self._model.filter(doctor_id=doctor_id).count()

    async def update_status(self, appointment_id: int, status: AppointmentStatus, doctor_notes: str | None = None) -> None:
        update_data: dict = {"status": status}
        if doctor_notes is not None:
            update_data["doctor_notes"] = doctor_notes
        await self._model.filter(id=appointment_id).update(**update_data)