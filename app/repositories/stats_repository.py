from collections import defaultdict
from datetime import date

from app.models.guides import Guide, GuideStatus
from app.models.health_logs import HealthLog, Mood
from app.models.messages import Message
from app.models.records import MedicalRecord


class StatsRepository:
    async def count_patient_records(self, patient_id: int) -> int:
        return await MedicalRecord.filter(patient_id=patient_id).count()

    async def count_unread_messages(self, user_id: int) -> int:
        return await Message.filter(receiver_id=user_id, is_read=False).count()

    async def count_patient_logs(self, patient_id: int) -> int:
        return await HealthLog.filter(patient_id=patient_id).count()

    async def get_pain_scores_since(self, patient_id: int, since: date) -> list[int]:
        return await HealthLog.filter(patient_id=patient_id, log_date__gte=since).values_list("pain_score", flat=True)

    async def get_pain_trend(self, patient_id: int, since: date) -> list[tuple[date, float]]:
        rows = (
            await HealthLog.filter(patient_id=patient_id, log_date__gte=since)
            .order_by("log_date")
            .values("log_date", "pain_score")
        )
        day_scores: dict[date, list[int]] = defaultdict(list)
        for row in rows:
            day_scores[row["log_date"]].append(row["pain_score"])
        return [(d, round(sum(scores) / len(scores), 1)) for d, scores in sorted(day_scores.items())]

    async def get_mood_distribution(self, patient_id: int, since: date) -> dict[str, int]:
        rows = await HealthLog.filter(patient_id=patient_id, log_date__gte=since).values_list("mood", flat=True)
        dist: dict[str, int] = {m.value: 0 for m in Mood}
        for mood in rows:
            dist[mood] = dist.get(mood, 0) + 1
        return dist

    async def count_doctor_patients(self, doctor_id: int) -> int:
        patient_ids = await MedicalRecord.filter(doctor_id=doctor_id).distinct().values_list("patient_id", flat=True)
        return len(set(patient_ids))

    async def count_doctor_records(self, doctor_id: int) -> int:
        return await MedicalRecord.filter(doctor_id=doctor_id).count()

    async def count_doctor_records_since(self, doctor_id: int, since: date) -> int:
        return await MedicalRecord.filter(doctor_id=doctor_id, visited_at__gte=since).count()

    async def count_pending_guides(self, doctor_id: int) -> int:
        return await Guide.filter(
            record__doctor_id=doctor_id,
            status__in=[GuideStatus.PENDING, GuideStatus.GENERATING],
        ).count()
