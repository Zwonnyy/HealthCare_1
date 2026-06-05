from datetime import date, timedelta

from fastapi import HTTPException
from starlette import status

from app.dtos.health_goals import HealthGoalCreateRequest, HealthGoalRecommendationResponse, HealthGoalUpdateRequest
from app.models.health_goal_history import HealthGoalHistory
from app.models.health_goals import GoalType, HealthGoal
from app.models.health_logs import HealthLog
from app.models.medication_checks import MedicationCheck
from app.models.records import Prescription
from app.models.users import User
from app.models.vitals import VitalRecord


class HealthGoalService:
    async def create(self, patient: User, data: HealthGoalCreateRequest) -> HealthGoal:
        return await HealthGoal.create(
            patient_id=patient.id,
            goal_type=data.goal_type,
            title=data.title,
            target_value=data.target_value,
            unit=data.unit,
            deadline=data.deadline,
        )

    async def list_goals(self, patient: User) -> list[HealthGoal]:
        return await HealthGoal.filter(patient_id=patient.id).order_by("-created_at")

    async def recommendations(self, patient: User) -> list[HealthGoalRecommendationResponse]:
        active_types = set(
            await HealthGoal.filter(patient_id=patient.id, achieved=False).values_list("goal_type", flat=True)
        )
        candidates = [
            *await _vital_goal_recommendations(patient=patient, active_types=active_types),
            *await _health_log_goal_recommendations(patient=patient, active_types=active_types),
            *await _medication_goal_recommendations(patient=patient, active_types=active_types),
        ]
        if GoalType.EXERCISE_DAYS not in active_types:
            candidates.append(
                HealthGoalRecommendationResponse(
                    goal_type=GoalType.EXERCISE_DAYS,
                    title="주 3회 가벼운 운동 실천",
                    target_value=12,
                    unit="일/월",
                    deadline=date.today() + timedelta(days=30),
                    reason="기본 건강 관리를 위해 무리 없는 월간 운동 목표를 추천합니다.",
                )
            )
        return candidates[:5]

    async def update(self, patient: User, goal_id: int, data: HealthGoalUpdateRequest) -> HealthGoal:
        goal = await HealthGoal.get_or_none(id=goal_id, patient_id=patient.id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="목표를 찾을 수 없습니다.")
        update_data = data.model_dump(exclude_none=True)
        if update_data:
            await HealthGoal.filter(id=goal_id).update(**update_data)
            goal = await HealthGoal.get(id=goal_id)
            if data.current_value is not None:
                await HealthGoalHistory.create(
                    goal_id=goal_id,
                    patient_id=patient.id,
                    recorded_value=data.current_value,
                )
        return goal

    async def delete(self, patient: User, goal_id: int) -> None:
        goal = await HealthGoal.get_or_none(id=goal_id, patient_id=patient.id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="목표를 찾을 수 없습니다.")
        await goal.delete()

    async def get_history(self, patient: User, goal_id: int) -> list[HealthGoalHistory]:
        goal = await HealthGoal.get_or_none(id=goal_id, patient_id=patient.id)
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="목표를 찾을 수 없습니다.")
        return await HealthGoalHistory.filter(goal_id=goal_id).order_by("recorded_at")


async def _vital_goal_recommendations(
    patient: User,
    active_types: set[GoalType],
) -> list[HealthGoalRecommendationResponse]:
    latest_vital = await VitalRecord.filter(patient_id=patient.id).order_by("-recorded_at").first()
    if not latest_vital:
        return []

    recommendations = []
    if (
        GoalType.BLOOD_PRESSURE not in active_types
        and latest_vital.systolic is not None
        and latest_vital.systolic >= 130
    ):
        recommendations.append(
            HealthGoalRecommendationResponse(
                goal_type=GoalType.BLOOD_PRESSURE,
                title="수축기 혈압 130 이하 관리",
                target_value=130,
                unit="mmHg",
                deadline=date.today() + timedelta(days=30),
                reason=f"최근 수축기 혈압이 {latest_vital.systolic}mmHg로 기록되어 혈압 관리 목표를 추천합니다.",
            )
        )
    if GoalType.WEIGHT not in active_types and latest_vital.weight is not None:
        recommendations.append(
            HealthGoalRecommendationResponse(
                goal_type=GoalType.WEIGHT,
                title="체중 주 1회 기록 유지",
                target_value=4,
                unit="회/월",
                deadline=date.today() + timedelta(days=30),
                reason="최근 체중 기록이 있어 꾸준한 추적 목표를 추천합니다.",
            )
        )
    return recommendations


async def _health_log_goal_recommendations(
    patient: User,
    active_types: set[GoalType],
) -> list[HealthGoalRecommendationResponse]:
    if GoalType.PAIN_SCORE in active_types:
        return []
    since = date.today() - timedelta(days=14)
    logs = await HealthLog.filter(patient_id=patient.id, log_date__gte=since)
    if not logs:
        return [
            HealthGoalRecommendationResponse(
                goal_type=GoalType.PAIN_SCORE,
                title="통증 점수 주 5회 기록",
                target_value=20,
                unit="회/월",
                deadline=date.today() + timedelta(days=30),
                reason="건강일지 기록이 아직 적어 증상 변화를 추적하는 목표를 추천합니다.",
            )
        ]
    avg_pain = sum(log.pain_score for log in logs) / len(logs)
    if avg_pain >= 5:
        return [
            HealthGoalRecommendationResponse(
                goal_type=GoalType.PAIN_SCORE,
                title="평균 통증 점수 4 이하 관리",
                target_value=4,
                unit="점",
                deadline=date.today() + timedelta(days=30),
                reason=f"최근 평균 통증 점수가 {avg_pain:.1f}점으로 높아 통증 관리 목표를 추천합니다.",
            )
        ]
    return []


async def _medication_goal_recommendations(
    patient: User,
    active_types: set[GoalType],
) -> list[HealthGoalRecommendationResponse]:
    if GoalType.CUSTOM in active_types:
        return []
    today = date.today()
    since = today - timedelta(days=29)
    prescriptions = await Prescription.all().prefetch_related("record")
    expected = 0
    for prescription in prescriptions:
        record = await prescription.record
        if record.patient_id != patient.id:
            continue
        start = max(record.visited_at.date(), since)
        end = min(record.visited_at.date() + timedelta(days=prescription.duration_days - 1), today)
        if start <= end:
            expected += (end - start).days + 1
    if expected == 0:
        return []
    checked = await MedicationCheck.filter(patient_id=patient.id, check_date__gte=since, check_date__lte=today).count()
    adherence = round((checked / expected) * 100, 1)
    if adherence >= 90:
        return []
    return [
        HealthGoalRecommendationResponse(
            goal_type=GoalType.CUSTOM,
            title="복약 체크 90% 유지",
            target_value=90,
            unit="%",
            deadline=date.today() + timedelta(days=30),
            reason=f"최근 복약 체크율이 {adherence}%라 복약 습관 개선 목표를 추천합니다.",
        )
    ]
