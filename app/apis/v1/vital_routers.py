from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.vitals import VitalCreateRequest, VitalResponse
from app.models.users import User
from app.services.vitals import VitalService

vital_router = APIRouter(prefix="/vitals", tags=["vitals"])


@vital_router.post("", response_model=VitalResponse, status_code=status.HTTP_201_CREATED)
async def record_vital(
    request: VitalCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[VitalService, Depends(VitalService)],
) -> Response:
    vital = await service.record(patient=patient, data=request)
    return Response(VitalResponse.model_validate(vital).model_dump(), status_code=status.HTTP_201_CREATED)


@vital_router.get("", response_model=list[VitalResponse], status_code=status.HTTP_200_OK)
async def list_vitals(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[VitalService, Depends(VitalService)],
    limit: int = 20,
) -> Response:
    vitals = await service.list_vitals(patient=patient, limit=limit)
    return Response([VitalResponse.model_validate(v).model_dump() for v in vitals], status_code=status.HTTP_200_OK)
