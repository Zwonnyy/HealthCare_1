from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.symptom_checks import SymptomCheckRequest, SymptomCheckResponse
from app.models.users import User
from app.services.symptom_checks import SymptomCheckService

symptom_check_router = APIRouter(prefix="/symptom-check", tags=["symptom-check"])


@symptom_check_router.post("", response_model=SymptomCheckResponse, status_code=status.HTTP_201_CREATED)
async def check_symptoms(
    request: SymptomCheckRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[SymptomCheckService, Depends(SymptomCheckService)],
) -> Response:
    result = await service.check(patient=patient, symptom_text=request.symptom_text)
    return Response(SymptomCheckResponse.model_validate(result).model_dump(), status_code=status.HTTP_201_CREATED)


@symptom_check_router.get("", response_model=list[SymptomCheckResponse], status_code=status.HTTP_200_OK)
async def list_symptom_checks(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[SymptomCheckService, Depends(SymptomCheckService)],
) -> Response:
    checks = await service.list_checks(patient=patient)
    return Response(
        [SymptomCheckResponse.model_validate(c).model_dump() for c in checks],
        status_code=status.HTTP_200_OK,
    )
