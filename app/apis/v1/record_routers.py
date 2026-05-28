from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import ORJSONResponse as Response
from fastapi.responses import StreamingResponse

from app.dependencies.security import get_doctor_user, get_patient_user, get_request_user
from app.dtos.guides import GuideResponse
from app.dtos.health_logs import HealthLogResponse
from app.dtos.messages import MessageResponse
from app.dtos.records import MedicalRecordCreateRequest, MedicalRecordResponse, PrescriptionResponse
from app.models.users import User
from app.services.guides import GuideService
from app.services.health_logs import HealthLogService
from app.services.messages import MessageService
from app.services.records import MedicalRecordService

record_router = APIRouter(prefix="/records", tags=["records"])


@record_router.post("", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    request: MedicalRecordCreateRequest,
    doctor: Annotated[User, Depends(get_doctor_user)],
    record_service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
) -> Response:
    record = await record_service.create_record(doctor=doctor, data=request)
    prescriptions = await record.prescriptions.all()
    data = MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        doctor_id=record.doctor_id,
        diagnosis=record.diagnosis,
        symptoms=record.symptoms,
        notes=record.notes,
        visited_at=record.visited_at,
        created_at=record.created_at,
        prescriptions=[PrescriptionResponse.model_validate(p) for p in prescriptions],
    )
    return Response(data.model_dump(), status_code=status.HTTP_201_CREATED)


@record_router.get("", response_model=list[MedicalRecordResponse], status_code=status.HTTP_200_OK)
async def get_records(
    user: Annotated[User, Depends(get_request_user)],
    record_service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
) -> Response:
    records = await record_service.get_records(user=user)
    result = []
    for record in records:
        prescriptions = await record.prescriptions.all()
        result.append(
            MedicalRecordResponse(
                id=record.id,
                patient_id=record.patient_id,
                doctor_id=record.doctor_id,
                diagnosis=record.diagnosis,
                symptoms=record.symptoms,
                notes=record.notes,
                visited_at=record.visited_at,
                created_at=record.created_at,
                prescriptions=[PrescriptionResponse.model_validate(p) for p in prescriptions],
            ).model_dump()
        )
    return Response(result, status_code=status.HTTP_200_OK)


@record_router.get("/{record_id}", response_model=MedicalRecordResponse, status_code=status.HTTP_200_OK)
async def get_record(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    record_service: Annotated[MedicalRecordService, Depends(MedicalRecordService)],
) -> Response:
    record = await record_service.get_record(user=user, record_id=record_id)
    prescriptions = await record.prescriptions.all()
    data = MedicalRecordResponse(
        id=record.id,
        patient_id=record.patient_id,
        doctor_id=record.doctor_id,
        diagnosis=record.diagnosis,
        symptoms=record.symptoms,
        notes=record.notes,
        visited_at=record.visited_at,
        created_at=record.created_at,
        prescriptions=[PrescriptionResponse.model_validate(p) for p in prescriptions],
    )
    return Response(data.model_dump(), status_code=status.HTTP_200_OK)


@record_router.post("/{record_id}/guides", response_model=GuideResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_guide(
    record_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    guide_service: Annotated[GuideService, Depends(GuideService)],
) -> Response:
    guide = await guide_service.request_guide(user=patient, record_id=record_id)
    return Response(GuideResponse.model_validate(guide).model_dump(), status_code=status.HTTP_202_ACCEPTED)


@record_router.post("/{record_id}/guides/stream", status_code=status.HTTP_200_OK)
async def stream_guide(
    record_id: int,
    patient: Annotated[User, Depends(get_patient_user)],
    guide_service: Annotated[GuideService, Depends(GuideService)],
) -> StreamingResponse:
    generator = await guide_service.stream_guide(user=patient, record_id=record_id)
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@record_router.get("/{record_id}/guides", response_model=list[GuideResponse], status_code=status.HTTP_200_OK)
async def get_record_guides(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    guide_service: Annotated[GuideService, Depends(GuideService)],
) -> Response:
    guides = await guide_service.get_record_guides(user=user, record_id=record_id)
    return Response([GuideResponse.model_validate(g).model_dump() for g in guides], status_code=status.HTTP_200_OK)


@record_router.get(
    "/{record_id}/health-logs", response_model=list[HealthLogResponse], status_code=status.HTTP_200_OK
)
async def get_record_health_logs(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    health_log_service: Annotated[HealthLogService, Depends(HealthLogService)],
) -> Response:
    logs = await health_log_service.get_record_logs(user=user, record_id=record_id)
    return Response([HealthLogResponse.model_validate(l).model_dump() for l in logs], status_code=status.HTTP_200_OK)


@record_router.get(
    "/{record_id}/messages", response_model=list[MessageResponse], status_code=status.HTTP_200_OK
)
async def get_record_messages(
    record_id: int,
    user: Annotated[User, Depends(get_request_user)],
    message_service: Annotated[MessageService, Depends(MessageService)],
) -> Response:
    messages = await message_service.get_record_messages(user=user, record_id=record_id)
    return Response(
        [MessageResponse.model_validate(m).model_dump() for m in messages], status_code=status.HTTP_200_OK
    )