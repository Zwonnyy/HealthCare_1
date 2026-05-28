from datetime import date, timedelta

from app.dtos.stats import (
    DoctorDashboardStats,
    HealthLogStats,
    MoodDistribution,
    PainTrendPoint,
    PatientDashboardStats,
)
from app.models.users import User
from app.repositories.stats_repository import StatsRepository


class StatsService:
    def __init__(self):
        self.repo = StatsRepository()

    async def get_patient_stats(self, user: User) -> PatientDashboardStats:
        today = date.today()
        week_ago = today - timedelta(days=6)
        month_ago = today - timedelta(days=29)
        trend_start = today - timedelta(days=13)

        total_records, unread_messages, total_logs = (
            await self.repo.count_patient_records(user.id),
            await self.repo.count_unread_messages(user.id),
            await self.repo.count_patient_logs(user.id),
        )

        scores_7d = await self.repo.get_pain_scores_since(user.id, week_ago)
        scores_30d = await self.repo.get_pain_scores_since(user.id, month_ago)
        trend = await self.repo.get_pain_trend(user.id, trend_start)
        mood_dist = await self.repo.get_mood_distribution(user.id, month_ago)

        return PatientDashboardStats(
            total_records=total_records,
            unread_messages=unread_messages,
            health_log_stats=HealthLogStats(
                total=total_logs,
                avg_pain_score_7d=round(sum(scores_7d) / len(scores_7d), 1) if scores_7d else None,
                avg_pain_score_30d=round(sum(scores_30d) / len(scores_30d), 1) if scores_30d else None,
                pain_trend_14d=[PainTrendPoint(date=d, avg_pain_score=avg) for d, avg in trend],
            ),
            mood_distribution_30d=MoodDistribution(**mood_dist),
        )

    async def get_doctor_stats(self, user: User) -> DoctorDashboardStats:
        today = date.today()
        month_ago = today - timedelta(days=29)

        total_patients, total_records, records_30d, unread_messages, pending_guides = (
            await self.repo.count_doctor_patients(user.id),
            await self.repo.count_doctor_records(user.id),
            await self.repo.count_doctor_records_since(user.id, month_ago),
            await self.repo.count_unread_messages(user.id),
            await self.repo.count_pending_guides(user.id),
        )

        return DoctorDashboardStats(
            total_patients=total_patients,
            total_records=total_records,
            records_last_30d=records_30d,
            unread_messages=unread_messages,
            pending_guides=pending_guides,
        )
