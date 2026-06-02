from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.health_goals import (
    HealthGoalCreateRequest,
    HealthGoalHistoryResponse,
    HealthGoalResponse,
    HealthGoalUpdateRequest,
)
from app.models.users import User
from app.services.health_goals import HealthGoalService

health_goal_router = APIRouter(prefix="/health-goals/goals", tags=["health-goals"])


@health_goal_router.post("", response_model=HealthGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    request: HealthGoalCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthGoalService, Depends(HealthGoalService)],
) -> Response:
    goal = await service.create(patient=patient, data=request)
    return Response(HealthGoalResponse.model_validate(goal).model_dump(), status_code=status.HTTP_201_CREATED)


@health_goal_router.get("", response_model=list[HealthGoalResponse], status_code=status.HTTP_200_OK)
async def list_goals(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthGoalService, Depends(HealthGoalService)],
) -> Response:
    goals = await service.list_goals(patient=patient)
    return Response([HealthGoalResponse.model_validate(g).model_dump() for g in goals], status_code=status.HTTP_200_OK)


@health_goal_router.patch("/{goal_id}", response_model=HealthGoalResponse, status_code=status.HTTP_200_OK)
async def update_goal(
    goal_id: int,
    request: HealthGoalUpdateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthGoalService, Depends(HealthGoalService)],
) -> Response:
    goal = await service.update(patient=patient, goal_id=goal_id, data=request)
    return Response(HealthGoalResponse.model_validate(goal).model_dump(), status_code=status.HTTP_200_OK)


@health_goal_router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthGoalService, Depends(HealthGoalService)],
) -> None:
    await service.delete(patient=patient, goal_id=goal_id)


@health_goal_router.get("/{goal_id}/history", response_model=list[HealthGoalHistoryResponse], status_code=status.HTTP_200_OK)
async def get_goal_history(
    goal_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthGoalService, Depends(HealthGoalService)],
) -> Response:
    history = await service.get_history(patient=patient, goal_id=goal_id)
    return Response(
        [HealthGoalHistoryResponse.model_validate(h).model_dump() for h in history],
        status_code=status.HTTP_200_OK,
    )
