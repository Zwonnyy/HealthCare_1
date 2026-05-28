from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user, get_request_user
from app.dtos.health_logs import (
    HealthLogAnalysisRequest,
    HealthLogAnalysisResponse,
    HealthLogCreateRequest,
    HealthLogResponse,
)
from app.dtos.pagination import PaginatedResponse, PaginationParams
from app.models.users import User
from app.services.health_logs import HealthLogService

health_log_router = APIRouter(prefix="/health-logs", tags=["health-logs"])


@health_log_router.post("", response_model=HealthLogResponse, status_code=status.HTTP_201_CREATED)
async def create_health_log(
    request: HealthLogCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> Response:
    log = await service.create_log(user=patient, data=request)
    return Response(HealthLogResponse.model_validate(log).model_dump(), status_code=status.HTTP_201_CREATED)


@health_log_router.get("", response_model=PaginatedResponse[HealthLogResponse], status_code=status.HTTP_200_OK)
async def get_my_health_logs(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
    pagination: Annotated[PaginationParams, Depends()],
) -> Response:
    logs, total = await service.get_my_logs(user=patient, offset=pagination.offset, limit=pagination.size)
    return Response(
        PaginatedResponse.create(
            items=[HealthLogResponse.model_validate(log) for log in logs],
            total=total,
            page=pagination.page,
            size=pagination.size,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@health_log_router.get("/{log_id}", response_model=HealthLogResponse, status_code=status.HTTP_200_OK)
async def get_health_log(
    log_id: int,
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> Response:
    log = await service.get_log(user=user, log_id=log_id)
    return Response(HealthLogResponse.model_validate(log).model_dump(), status_code=status.HTTP_200_OK)


@health_log_router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_log(
    log_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> None:
    await service.delete_log(user=patient, log_id=log_id)


@health_log_router.post("/analyze", response_model=HealthLogAnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_analysis(
    request: HealthLogAnalysisRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> Response:
    analysis = await service.request_analysis(user=patient, record_id=request.record_id)
    return Response(
        HealthLogAnalysisResponse.model_validate(analysis).model_dump(), status_code=status.HTTP_202_ACCEPTED
    )


@health_log_router.get(
    "/analyses/{analysis_id}", response_model=HealthLogAnalysisResponse, status_code=status.HTTP_200_OK
)
async def get_analysis(
    analysis_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> Response:
    analysis = await service.get_analysis(user=patient, analysis_id=analysis_id)
    return Response(HealthLogAnalysisResponse.model_validate(analysis).model_dump(), status_code=status.HTTP_200_OK)
