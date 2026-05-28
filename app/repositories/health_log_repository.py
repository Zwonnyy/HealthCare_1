from datetime import date

from app.models.health_logs import HealthLog, HealthLogAnalysis, Mood


class HealthLogRepository:
    def __init__(self):
        self._log_model = HealthLog
        self._analysis_model = HealthLogAnalysis

    async def create_log(
        self,
        patient_id: int,
        log_date: date,
        pain_score: int,
        mood: Mood,
        symptoms_text: str,
        record_id: int | None = None,
        notes: str | None = None,
    ) -> HealthLog:
        return await self._log_model.create(
            patient_id=patient_id,
            record_id=record_id,
            log_date=log_date,
            pain_score=pain_score,
            mood=mood,
            symptoms_text=symptoms_text,
            notes=notes,
        )

    async def get_log(self, log_id: int) -> HealthLog | None:
        return await self._log_model.get_or_none(id=log_id)

    async def get_patient_logs(self, patient_id: int) -> list[HealthLog]:
        return await self._log_model.filter(patient_id=patient_id).order_by("-log_date")

    async def get_record_logs(self, record_id: int) -> list[HealthLog]:
        return await self._log_model.filter(record_id=record_id).order_by("log_date")

    async def delete_log(self, log_id: int) -> None:
        await self._log_model.filter(id=log_id).delete()

    async def create_analysis(self, patient_id: int, record_id: int | None) -> HealthLogAnalysis:
        return await self._analysis_model.create(patient_id=patient_id, record_id=record_id)

    async def get_analysis(self, analysis_id: int) -> HealthLogAnalysis | None:
        return await self._analysis_model.get_or_none(id=analysis_id)
