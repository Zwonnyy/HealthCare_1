from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse as Response

from app.dependencies.security import get_doctor_user, get_patient_user, get_request_user
from app.dtos.health_insights import (
    ClinicalNoteDraftResponse,
    HealthRiskResponse,
    MedicationAdherenceResponse,
    MedicationPatternResponse,
    PatientRiskQueueResponse,
    PatientTimelineResponse,
    PreVisitQuestionnaireCreateRequest,
    PreVisitQuestionnaireResponse,
)
from app.models.users import User
from app.services.health_insights import HealthInsightService

health_insight_router = APIRouter(prefix="/health-insights", tags=["health-insights"])


@health_insight_router.get("/risk", response_model=HealthRiskResponse, status_code=status.HTTP_200_OK)
async def get_health_risk(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> Response:
    result = await service.assess_risk(patient=patient, days=days)
    await service.notify_risk_alerts(patient=patient, risk=result)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@health_insight_router.get(
    "/medication-adherence", response_model=MedicationAdherenceResponse, status_code=status.HTTP_200_OK
)
async def get_medication_adherence(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> Response:
    result = await service.medication_adherence(patient=patient, days=days)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@health_insight_router.get(
    "/medication-patterns", response_model=MedicationPatternResponse, status_code=status.HTTP_200_OK
)
async def get_medication_patterns(
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> Response:
    result = await service.medication_patterns(patient=patient, days=days)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@health_insight_router.get("/risk-queue", response_model=PatientRiskQueueResponse, status_code=status.HTTP_200_OK)
async def get_patient_risk_queue(
    doctor: Annotated[User, Depends(get_doctor_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> Response:
    result = await service.patient_risk_queue(doctor=doctor, days=days)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@health_insight_router.post(
    "/appointments/{appointment_id}/pre-visit",
    response_model=PreVisitQuestionnaireResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pre_visit_questionnaire(
    appointment_id: int,
    request: PreVisitQuestionnaireCreateRequest,
    patient: Annotated[User, Depends(get_patient_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
) -> Response:
    result = await service.create_pre_visit(patient=patient, appointment_id=appointment_id, data=request)
    return Response(
        PreVisitQuestionnaireResponse.model_validate(result).model_dump(), status_code=status.HTTP_201_CREATED
    )


@health_insight_router.get(
    "/pre-visits",
    response_model=list[PreVisitQuestionnaireResponse],
    status_code=status.HTTP_200_OK,
)
async def list_pre_visit_questionnaires(
    user: Annotated[User, Depends(get_request_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    appointment_id: int | None = None,
) -> Response:
    results = await service.list_pre_visits(user=user, appointment_id=appointment_id)
    return Response(
        [PreVisitQuestionnaireResponse.model_validate(result).model_dump() for result in results],
        status_code=status.HTTP_200_OK,
    )


@health_insight_router.get(
    "/patients/{patient_id}/timeline",
    response_model=PatientTimelineResponse,
    status_code=status.HTTP_200_OK,
)
async def get_patient_timeline(
    patient_id: int,
    doctor: Annotated[User, Depends(get_doctor_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
    days: Annotated[int, Query(ge=7, le=365)] = 90,
) -> Response:
    result = await service.patient_timeline(doctor=doctor, patient_id=patient_id, days=days)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)


@health_insight_router.post(
    "/pre-visits/{pre_visit_id}/clinical-note-draft",
    response_model=ClinicalNoteDraftResponse,
    status_code=status.HTTP_200_OK,
)
async def create_clinical_note_draft(
    pre_visit_id: int,
    doctor: Annotated[User, Depends(get_doctor_user)],
    service: Annotated[HealthInsightService, Depends(HealthInsightService)],
) -> Response:
    result = await service.clinical_note_draft(doctor=doctor, pre_visit_id=pre_visit_id)
    return Response(result.model_dump(), status_code=status.HTTP_200_OK)
