from fastapi import HTTPException
from starlette import status

from app.dtos.health_goals import HealthGoalCreateRequest, HealthGoalUpdateRequest
from app.models.health_goal_history import HealthGoalHistory
from app.models.health_goals import HealthGoal
from app.models.users import User


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
