from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.medication_checks import TodayMedicationItem
from app.dtos.records import PrescriptionResponse
from app.models.users import User
from app.services.medication_checks import MedicationCheckService

medication_check_router = APIRouter(prefix="/medication-checks", tags=["medication-checks"])


@medication_check_router.get("/today", response_model=list[TodayMedicationItem], status_code=status.HTTP_200_OK)
async def get_today_medications(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationCheckService, Depends(MedicationCheckService)],
) -> Response:
    items = await service.get_today_medications(patient=patient)
    result = [
        TodayMedicationItem(
            prescription=PrescriptionResponse.model_validate(item["prescription"]),
            checked=item["checked"],
        )
        for item in items
    ]
    return Response([r.model_dump() for r in result], status_code=status.HTTP_200_OK)


@medication_check_router.post("/{prescription_id}/toggle", status_code=status.HTTP_200_OK)
async def toggle_medication_check(
    prescription_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationCheckService, Depends(MedicationCheckService)],
) -> Response:
    checked = await service.toggle_check(patient=patient, prescription_id=prescription_id)
    return Response({"checked": checked}, status_code=status.HTTP_200_OK)
