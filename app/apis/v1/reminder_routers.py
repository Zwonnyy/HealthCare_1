from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_patient_user
from app.dtos.medication_reminders import ReminderCreateRequest, ReminderResponse, ReminderUpdateRequest
from app.models.users import User
from app.services.medication_reminders import MedicationReminderService

reminder_router = APIRouter(prefix="/reminders", tags=["reminders"])


@reminder_router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
async def create_reminder(
    request: ReminderCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationReminderService, Depends(MedicationReminderService)],
) -> Response:
    reminder = await service.create(patient=patient, data=request)
    return Response(ReminderResponse.model_validate(reminder).model_dump(), status_code=status.HTTP_201_CREATED)


@reminder_router.get("", response_model=list[ReminderResponse], status_code=status.HTTP_200_OK)
async def list_reminders(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationReminderService, Depends(MedicationReminderService)],
) -> Response:
    reminders = await service.list_reminders(patient=patient)
    return Response(
        [ReminderResponse.model_validate(r).model_dump() for r in reminders],
        status_code=status.HTTP_200_OK,
    )


@reminder_router.patch("/{reminder_id}", response_model=ReminderResponse, status_code=status.HTTP_200_OK)
async def update_reminder(
    reminder_id: int,
    request: ReminderUpdateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationReminderService, Depends(MedicationReminderService)],
) -> Response:
    reminder = await service.update(patient=patient, reminder_id=reminder_id, data=request)
    return Response(ReminderResponse.model_validate(reminder).model_dump(), status_code=status.HTTP_200_OK)


@reminder_router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[MedicationReminderService, Depends(MedicationReminderService)],
) -> None:
    await service.delete(patient=patient, reminder_id=reminder_id)
