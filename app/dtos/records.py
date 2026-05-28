from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

from app.dtos.base import BaseSerializerModel


class PrescriptionCreateRequest(BaseModel):
    medication_name: Annotated[str, Field(max_length=100, description="약물명")]
    dosage: Annotated[str, Field(max_length=50, description="용량 (예: 500mg)")]
    frequency: Annotated[str, Field(max_length=50, description="복용 횟수 (예: 1일 3회)")]
    duration_days: Annotated[int, Field(gt=0, description="복용 기간 (일)")]
    instructions: str | None = Field(None, description="특이사항")


class MedicalRecordCreateRequest(BaseModel):
    patient_id: int = Field(description="환자 ID")
    diagnosis: str = Field(description="진단명")
    symptoms: str = Field(description="주요 증상")
    notes: str | None = Field(None, description="의사 메모")
    visited_at: datetime = Field(description="진료 일시")
    prescriptions: list[PrescriptionCreateRequest] = Field(default_factory=list)


class PrescriptionResponse(BaseSerializerModel):
    id: int
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    instructions: str | None


class MedicalRecordResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    diagnosis: str
    symptoms: str
    notes: str | None
    visited_at: datetime
    created_at: datetime
    prescriptions: list[PrescriptionResponse] = []