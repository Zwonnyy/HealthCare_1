from datetime import datetime

from app.models.records import MedicalRecord, Prescription


class RecordRepository:
    def __init__(self):
        self._model = MedicalRecord
        self._prescription_model = Prescription

    async def create_record(
        self,
        patient_id: int,
        doctor_id: int,
        diagnosis: str,
        symptoms: str,
        visited_at: datetime,
        notes: str | None = None,
    ) -> MedicalRecord:
        return await self._model.create(
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            symptoms=symptoms,
            notes=notes,
            visited_at=visited_at,
        )

    async def create_prescription(
        self,
        record_id: int,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration_days: int,
        instructions: str | None = None,
    ) -> Prescription:
        return await self._prescription_model.create(
            record_id=record_id,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            instructions=instructions,
        )

    async def get_record(self, record_id: int) -> MedicalRecord | None:
        return await self._model.get_or_none(id=record_id)

    async def get_patient_records(self, patient_id: int) -> list[MedicalRecord]:
        return await self._model.filter(patient_id=patient_id).order_by("-visited_at")

    async def get_doctor_records(self, doctor_id: int) -> list[MedicalRecord]:
        return await self._model.filter(doctor_id=doctor_id).order_by("-visited_at")
