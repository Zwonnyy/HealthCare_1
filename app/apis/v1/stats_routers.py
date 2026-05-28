from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_doctor_user, get_patient_user
from app.dtos.stats import DoctorDashboardStats, PatientDashboardStats
from app.models.users import User
from app.services.stats import StatsService

stats_router = APIRouter(prefix="/stats", tags=["stats"])


@stats_router.get("/patient", response_model=PatientDashboardStats, status_code=status.HTTP_200_OK)
async def get_patient_stats(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[StatsService, Depends(StatsService)],
) -> Response:
    stats = await service.get_patient_stats(user=patient)
    return Response(stats.model_dump(), status_code=status.HTTP_200_OK)


@stats_router.get("/doctor", response_model=DoctorDashboardStats, status_code=status.HTTP_200_OK)
async def get_doctor_stats(
    doctor: Annotated[User, Depends(get_doctor_user)],
    service: Annotated[StatsService, Depends(StatsService)],
) -> Response:
    stats = await service.get_doctor_stats(user=doctor)
    return Response(stats.model_dump(), status_code=status.HTTP_200_OK)
