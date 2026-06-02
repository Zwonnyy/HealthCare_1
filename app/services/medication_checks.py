from datetime import date, timedelta

from app.models.records import Prescription
from app.models.users import User
from app.repositories.medication_check_repository import MedicationCheckRepository


class MedicationCheckService:
    def __init__(self):
        self.repo = MedicationCheckRepository()

    async def get_today_medications(self, patient: User) -> list[dict]:
        today = date.today()
        # 오늘 복약 중인 처방전 조회 (visited_at <= today <= visited_at + duration_days)
        all_prescriptions = await Prescription.all().prefetch_related("record")
        active: list[Prescription] = []
        for p in all_prescriptions:
            record = await p.record
            if record.patient_id != patient.id:
                continue
            end_date = record.visited_at.date() + timedelta(days=p.duration_days)
            if record.visited_at.date() <= today <= end_date:
                active.append(p)

        checked_ids = await self.repo.get_checked_ids(patient.id, today)
        return [
            {
                "prescription": p,
                "checked": p.id in checked_ids,
            }
            for p in active
        ]

    async def toggle_check(self, patient: User, prescription_id: int) -> bool:
        today = date.today()
        checked_ids = await self.repo.get_checked_ids(patient.id, today)
        if prescription_id in checked_ids:
            await self.repo.uncheck(patient.id, prescription_id, today)
            return False
        else:
            await self.repo.check(patient.id, prescription_id, today)
            return True
