from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_doctor_user, get_patient_user, get_request_user
from app.dtos.appointments import AppointmentCreateRequest, AppointmentResponse, AppointmentUpdateRequest
from app.dtos.pagination import PaginatedResponse, PaginationParams
from app.models.users import User
from app.services.appointments import AppointmentService

appointment_router = APIRouter(prefix="/appointments", tags=["appointments"])


@appointment_router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    request: AppointmentCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[AppointmentService, Depends(AppointmentService)],
) -> Response:
    appt = await service.create_appointment(patient=patient, data=request)
    return Response(AppointmentResponse.model_validate(appt).model_dump(), status_code=status.HTTP_201_CREATED)


@appointment_router.get("", response_model=PaginatedResponse[AppointmentResponse], status_code=status.HTTP_200_OK)
async def get_appointments(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[AppointmentService, Depends(AppointmentService)],
    pagination: Annotated[PaginationParams, Depends()],
) -> Response:
    items, total = await service.get_appointments(user=user, offset=pagination.offset, limit=pagination.size)
    return Response(
        PaginatedResponse.create(
            items=[AppointmentResponse.model_validate(a) for a in items],
            total=total,
            page=pagination.page,
            size=pagination.size,
        ).model_dump(),
        status_code=status.HTTP_200_OK,
    )


@appointment_router.patch("/{appointment_id}", response_model=AppointmentResponse, status_code=status.HTTP_200_OK)
async def update_appointment(
    appointment_id: int,
    request: AppointmentUpdateRequest,
    doctor: Annotated[User, Depends(get_doctor_user)],
    service: Annotated[AppointmentService, Depends(AppointmentService)],
) -> Response:
    appt = await service.update_appointment(doctor=doctor, appointment_id=appointment_id, data=request)
    return Response(AppointmentResponse.model_validate(appt).model_dump(), status_code=status.HTTP_200_OK)


@appointment_router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_appointment(
    appointment_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[AppointmentService, Depends(AppointmentService)],
) -> None:
    await service.cancel_appointment(patient=patient, appointment_id=appointment_id)
