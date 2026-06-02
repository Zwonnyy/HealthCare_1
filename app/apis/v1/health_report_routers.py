from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.health_reports import HealthReportResponse
from app.models.users import User
from app.services.health_reports import HealthReportService

health_report_router = APIRouter(prefix="/health-reports", tags=["health-reports"])


@health_report_router.post("/generate", response_model=HealthReportResponse, status_code=status.HTTP_200_OK)
async def generate_report(
    year: int,
    month: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthReportService, Depends(HealthReportService)],
) -> Response:
    report = await service.generate(patient=patient, year=year, month=month)
    return Response(HealthReportResponse.model_validate(report).model_dump(), status_code=status.HTTP_200_OK)


@health_report_router.get("", response_model=list[HealthReportResponse], status_code=status.HTTP_200_OK)
async def list_reports(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthReportService, Depends(HealthReportService)],
) -> Response:
    reports = await service.list_reports(patient=patient)
    return Response(
        [HealthReportResponse.model_validate(r).model_dump() for r in reports],
        status_code=status.HTTP_200_OK,
    )
