import logging
from datetime import date, timedelta

from fastapi import HTTPException
from google import genai
from google.genai import types
from starlette import status

from app.core import config
from app.dtos.health_insights import (
    HealthRiskResponse,
    MedicationAdherenceItem,
    MedicationAdherenceResponse,
    PreVisitQuestionnaireCreateRequest,
    RiskSignal,
)
from app.models.appointments import Appointment
from app.models.health_logs import HealthLog, Mood
from app.models.medication_checks import MedicationCheck
from app.models.pre_visit_questionnaires import PreVisitQuestionnaire
from app.models.records import Prescription
from app.models.symptom_checks import SymptomCheck, UrgencyLevel
from app.models.users import User, UserRole
from app.models.vitals import VitalRecord

logger = logging.getLogger(__name__)

_PRE_VISIT_SYSTEM = (
    "당신은 진료 전 문진 내용을 의사가 빠르게 볼 수 있도록 정리하는 의료 보조 AI입니다. "
    "진단을 내리지 말고, 확인해야 할 질문과 위험 신호를 한국어로 간결하게 요약하세요."
)


class HealthInsightService:
    async def assess_risk(self, patient: User, days: int = 30) -> HealthRiskResponse:  # noqa: C901
        since = date.today() - timedelta(days=days)
        signals: list[RiskSignal] = []

        logs = await HealthLog.filter(patient_id=patient.id, log_date__gte=since).order_by("-log_date")
        vitals = await VitalRecord.filter(patient_id=patient.id, recorded_at__gte=since).order_by("-recorded_at")
        symptoms = await SymptomCheck.filter(patient_id=patient.id, created_at__gte=since).order_by("-created_at")

        if logs:
            avg_pain = sum(log.pain_score for log in logs) / len(logs)
            bad_moods = sum(1 for log in logs if log.mood in (Mood.BAD, Mood.TERRIBLE))
            if avg_pain >= 7:
                signals.append(
                    RiskSignal(label="통증 상승", detail=f"최근 평균 통증 점수 {avg_pain:.1f}점", severity=25)
                )
            elif avg_pain >= 5:
                signals.append(
                    RiskSignal(label="통증 주의", detail=f"최근 평균 통증 점수 {avg_pain:.1f}점", severity=12)
                )
            if bad_moods >= 3:
                signals.append(RiskSignal(label="기분 악화", detail=f"나쁨/매우 나쁨 기록 {bad_moods}회", severity=12))

        abnormal_vitals = 0
        for vital in vitals:
            if vital.systolic and vital.systolic >= 140:
                abnormal_vitals += 1
            if vital.diastolic and vital.diastolic >= 90:
                abnormal_vitals += 1
            if vital.blood_sugar and vital.blood_sugar >= 180:
                abnormal_vitals += 1
            if vital.heart_rate and (vital.heart_rate < 50 or vital.heart_rate > 110):
                abnormal_vitals += 1
        if abnormal_vitals:
            severity = min(30, 8 + abnormal_vitals * 4)
            signals.append(
                RiskSignal(label="바이탈 이상", detail=f"기준 초과 항목 {abnormal_vitals}건", severity=severity)
            )

        high_symptoms = sum(1 for symptom in symptoms if symptom.urgency == UrgencyLevel.HIGH)
        medium_symptoms = sum(1 for symptom in symptoms if symptom.urgency == UrgencyLevel.MEDIUM)
        if high_symptoms:
            signals.append(RiskSignal(label="고긴급 증상", detail=f"HIGH 평가 {high_symptoms}회", severity=30))
        elif medium_symptoms:
            signals.append(RiskSignal(label="진료 권고 증상", detail=f"MEDIUM 평가 {medium_symptoms}회", severity=15))

        score = min(100, sum(signal.severity for signal in signals))
        if score >= 60:
            risk_level = "높음"
        elif score >= 30:
            risk_level = "주의"
        else:
            risk_level = "낮음"

        recommendations = [
            "증상이 급격히 악화되거나 흉통, 호흡곤란, 의식 변화가 있으면 즉시 응급 진료를 받으세요.",
            "최근 기록을 꾸준히 남기면 AI 리스크 예측 정확도가 올라갑니다.",
        ]
        if risk_level != "낮음":
            recommendations.insert(0, "담당 의료진에게 최근 증상과 바이탈 변화를 공유하세요.")

        summary = f"최근 {days}일 데이터 기준 건강 리스크는 '{risk_level}'입니다."
        return HealthRiskResponse(
            risk_level=risk_level,
            score=score,
            summary=summary,
            signals=signals,
            recommendations=recommendations,
        )

    async def medication_adherence(self, patient: User, days: int = 30) -> MedicationAdherenceResponse:
        today = date.today()
        since = today - timedelta(days=days - 1)
        prescriptions = await Prescription.all().prefetch_related("record")
        items: list[MedicationAdherenceItem] = []

        for prescription in prescriptions:
            record = await prescription.record
            if record.patient_id != patient.id:
                continue
            start = max(record.visited_at.date(), since)
            end = min(record.visited_at.date() + timedelta(days=prescription.duration_days - 1), today)
            if start > end:
                continue
            expected_days = (end - start).days + 1
            checked_days = await MedicationCheck.filter(
                patient_id=patient.id,
                prescription_id=prescription.id,
                check_date__gte=start,
                check_date__lte=end,
            ).count()
            rate = round((checked_days / expected_days) * 100, 1) if expected_days else 0
            items.append(
                MedicationAdherenceItem(
                    prescription_id=prescription.id,
                    medication_name=prescription.medication_name,
                    expected_days=expected_days,
                    checked_days=checked_days,
                    adherence_rate=rate,
                )
            )

        total_expected = sum(item.expected_days for item in items)
        total_checked = sum(item.checked_days for item in items)
        overall = round((total_checked / total_expected) * 100, 1) if total_expected else 0
        if not items:
            summary = "분석할 처방 복약 기록이 아직 없습니다."
        elif overall >= 90:
            summary = "복약 순응도가 안정적입니다."
        elif overall >= 70:
            summary = "복약 누락이 일부 있습니다. 놓치는 시간대를 확인해보세요."
        else:
            summary = "복약 누락이 잦습니다. 알림 시간 조정이나 의료진 상담을 권장합니다."

        return MedicationAdherenceResponse(period_days=days, overall_rate=overall, summary=summary, items=items)

    async def create_pre_visit(
        self,
        patient: User,
        appointment_id: int,
        data: PreVisitQuestionnaireCreateRequest,
    ) -> PreVisitQuestionnaire:
        appointment = await Appointment.get_or_none(id=appointment_id)
        if not appointment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="예약을 찾을 수 없습니다.")
        if appointment.patient_id != patient.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        summary = await _summarize_pre_visit(data)
        return await PreVisitQuestionnaire.create(
            appointment_id=appointment_id,
            patient_id=patient.id,
            symptoms=data.symptoms,
            onset=data.onset,
            severity=data.severity,
            medications=data.medications,
            history=data.history,
            questions=data.questions,
            ai_summary=summary,
        )

    async def list_pre_visits(self, user: User, appointment_id: int | None = None) -> list[PreVisitQuestionnaire]:
        query = PreVisitQuestionnaire.all().order_by("-created_at")
        if user.role == UserRole.PATIENT:
            query = query.filter(patient_id=user.id)
        else:
            appointments = await Appointment.filter(doctor_id=user.id).values_list("id", flat=True)
            query = query.filter(appointment_id__in=list(appointments))
        if appointment_id is not None:
            query = query.filter(appointment_id=appointment_id)
        return await query.limit(50)


async def _summarize_pre_visit(data: PreVisitQuestionnaireCreateRequest) -> str:
    fallback = (
        f"주요 증상: {data.symptoms}\n"
        f"시작 시점: {data.onset or '미입력'}\n"
        f"심각도: {data.severity if data.severity is not None else '미입력'} / 10\n"
        f"복용약: {data.medications or '미입력'}\n"
        f"과거력: {data.history or '미입력'}\n"
        f"환자 질문: {data.questions or '미입력'}"
    )
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=_PRE_VISIT_SYSTEM),
            contents=(
                f"{fallback}\n\n"
                "다음 항목으로 요약하세요: 1) 핵심 호소 2) 확인할 위험 신호 3) 의사가 물어볼 질문 4) 환자 질문."
            ),
        )
        return (response.text or fallback).strip()
    except Exception as e:
        logger.warning("Pre-visit summary failed: %s", e)
        return fallback
