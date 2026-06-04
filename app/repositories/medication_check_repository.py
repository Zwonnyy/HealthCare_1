from datetime import date

from app.models.medication_checks import MedicationCheck


class MedicationCheckRepository:
    def __init__(self):
        self._model = MedicationCheck

    async def get_checked_ids(self, patient_id: int, check_date: date) -> set[int]:
        checks = await self._model.filter(patient_id=patient_id, check_date=check_date).values_list(
            "prescription_id", flat=True
        )
        return set(checks)

    async def check(self, patient_id: int, prescription_id: int, check_date: date) -> MedicationCheck:
        obj, _ = await self._model.get_or_create(
            patient_id=patient_id,
            prescription_id=prescription_id,
            check_date=check_date,
        )
        return obj

    async def uncheck(self, patient_id: int, prescription_id: int, check_date: date) -> None:
        await self._model.filter(patient_id=patient_id, prescription_id=prescription_id, check_date=check_date).delete()
