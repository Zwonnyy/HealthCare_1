import json
import logging
from datetime import UTC, date, datetime, time, timedelta

from fastapi import HTTPException
from google import genai
from google.genai import types
from starlette import status

from app.core import config
from app.dtos.health_insights import (
    ClinicalNoteDraftResponse,
    HealthRiskResponse,
    MedicationAdherenceItem,
    MedicationAdherenceResponse,
    PatientTimelineItem,
    PatientTimelineResponse,
    PreVisitQuestionnaireCreateRequest,
    RiskSignal,
)
from app.models.appointments import Appointment
from app.models.health_logs import HealthLog, Mood
from app.models.medication_checks import MedicationCheck
from app.models.notifications import Notification, NotificationType
from app.models.pre_visit_questionnaires import PreVisitQuestionnaire
from app.models.records import MedicalRecord, Prescription
from app.models.symptom_checks import SymptomCheck, UrgencyLevel
from app.models.users import User, UserRole
from app.models.vitals import VitalRecord

logger = logging.getLogger(__name__)

_PRE_VISIT_SYSTEM = (
    "당신은 진료 전 문진 내용을 의사가 빠르게 볼 수 있도록 정리하는 의료 보조 AI입니다. "
    "진단을 내리지 말고, 확인해야 할 질문과 위험 신호를 한국어로 간결하게 요약하세요."
)

_CLINICAL_NOTE_SYSTEM = (
    "당신은 의사의 진료기록 작성을 돕는 의료 문서 보조 AI입니다. "
    "확정 진단을 내리지 말고 환자 문진 내용에 근거한 SOAP 형식 초안을 한국어로 작성하세요."
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

    async def notify_risk_alerts(self, patient: User, risk: HealthRiskResponse) -> int:
        if risk.risk_level == "낮음":
            return 0

        title = f"건강 리스크 {risk.risk_level} 알림"
        body = f"{patient.name}님의 {risk.summary} 주요 신호: {_format_risk_signal_summary(risk)}"
        recipients = {patient.id, *await _related_doctor_ids(patient.id)}
        created = 0
        for user_id in recipients:
            if await _has_recent_risk_alert(user_id=user_id, title=title):
                continue
            await Notification.create(
                user_id=user_id,
                notification_type=NotificationType.HEALTH_RISK_ALERT,
                title=title,
                body=body,
            )
            created += 1
        return created

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

    async def patient_timeline(self, doctor: User, patient_id: int, days: int = 90) -> PatientTimelineResponse:
        patient = await User.get_or_none(id=patient_id, role=UserRole.PATIENT)
        if not patient:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="환자를 찾을 수 없습니다.")

        has_record = await MedicalRecord.filter(doctor_id=doctor.id, patient_id=patient_id).exists()
        has_appointment = await Appointment.filter(doctor_id=doctor.id, patient_id=patient_id).exists()
        if not has_record and not has_appointment:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        since_date = date.today() - timedelta(days=days)
        since_datetime = datetime.combine(since_date, time.min)
        items = [
            *await _record_timeline_items(doctor_id=doctor.id, patient_id=patient_id, since=since_datetime),
            *await _health_log_timeline_items(patient_id=patient_id, since=since_date),
            *await _vital_timeline_items(patient_id=patient_id, since=since_datetime),
            *await _symptom_timeline_items(patient_id=patient_id, since=since_datetime),
            *await _pre_visit_timeline_items(doctor_id=doctor.id, patient_id=patient_id, since=since_datetime),
        ]

        items.sort(key=lambda item: item.occurred_at, reverse=True)
        return PatientTimelineResponse(
            patient_id=patient.id,
            patient_name=patient.name,
            period_days=days,
            items=items[:100],
        )

    async def clinical_note_draft(self, doctor: User, pre_visit_id: int) -> ClinicalNoteDraftResponse:
        pre_visit = await PreVisitQuestionnaire.get_or_none(id=pre_visit_id)
        if not pre_visit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="문진을 찾을 수 없습니다.")

        appointment = await pre_visit.appointment
        if appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        return await _generate_clinical_note_draft(pre_visit)


async def _record_timeline_items(doctor_id: int, patient_id: int, since: datetime) -> list[PatientTimelineItem]:
    records = await MedicalRecord.filter(
        doctor_id=doctor_id,
        patient_id=patient_id,
        visited_at__gte=since,
    ).order_by("-visited_at")
    items: list[PatientTimelineItem] = []
    for record in records:
        prescriptions = await record.prescriptions.all()
        medication_names = ", ".join(p.medication_name for p in prescriptions) or "처방 없음"
        items.append(
            PatientTimelineItem(
                id=record.id,
                type="record",
                title=f"진료 기록 · {record.diagnosis}",
                summary=f"{record.symptoms} / 처방: {medication_names}",
                occurred_at=record.visited_at,
                metadata={"diagnosis": record.diagnosis, "prescription_count": len(prescriptions)},
            )
        )
    return items


async def _health_log_timeline_items(patient_id: int, since: date) -> list[PatientTimelineItem]:
    logs = await HealthLog.filter(patient_id=patient_id, log_date__gte=since).order_by("-log_date")
    return [
        PatientTimelineItem(
            id=log.id,
            type="health_log",
            title=f"건강일지 · 통증 {log.pain_score}/10",
            summary=log.symptoms_text,
            occurred_at=datetime.combine(log.log_date, time.min),
            metadata={"pain_score": log.pain_score, "mood": log.mood.value},
        )
        for log in logs
    ]


async def _vital_timeline_items(patient_id: int, since: datetime) -> list[PatientTimelineItem]:
    vitals = await VitalRecord.filter(patient_id=patient_id, recorded_at__gte=since).order_by("-recorded_at")
    return [
        PatientTimelineItem(
            id=vital.id,
            type="vital",
            title="바이탈 기록",
            summary=_format_vital_summary(vital),
            occurred_at=vital.recorded_at,
            metadata={
                "systolic": vital.systolic,
                "diastolic": vital.diastolic,
                "blood_sugar": vital.blood_sugar,
                "heart_rate": vital.heart_rate,
                "weight": vital.weight,
            },
        )
        for vital in vitals
    ]


async def _symptom_timeline_items(patient_id: int, since: datetime) -> list[PatientTimelineItem]:
    symptoms = await SymptomCheck.filter(patient_id=patient_id, created_at__gte=since).order_by("-created_at")
    return [
        PatientTimelineItem(
            id=symptom.id,
            type="symptom_check",
            title=f"증상 체크 · {symptom.urgency or '평가 없음'}",
            summary=symptom.symptom_text,
            occurred_at=symptom.created_at,
            metadata={
                "urgency": symptom.urgency.value if symptom.urgency else None,
                "suggest_appointment": symptom.suggest_appointment,
            },
        )
        for symptom in symptoms
    ]


async def _pre_visit_timeline_items(doctor_id: int, patient_id: int, since: datetime) -> list[PatientTimelineItem]:
    pre_visits = await PreVisitQuestionnaire.filter(patient_id=patient_id, created_at__gte=since).order_by(
        "-created_at"
    )
    items: list[PatientTimelineItem] = []
    for pre_visit in pre_visits:
        appointment = await pre_visit.appointment
        if appointment.doctor_id != doctor_id:
            continue
        items.append(
            PatientTimelineItem(
                id=pre_visit.id,
                type="pre_visit",
                title=f"진료 전 문진 · 예약 #{pre_visit.appointment_id}",
                summary=pre_visit.ai_summary or pre_visit.symptoms,
                occurred_at=pre_visit.created_at,
                metadata={"appointment_id": pre_visit.appointment_id, "severity": pre_visit.severity},
            )
        )
    return items


def _format_vital_summary(vital: VitalRecord) -> str:
    parts = []
    if vital.systolic or vital.diastolic:
        parts.append(f"혈압 {vital.systolic or '-'} / {vital.diastolic or '-'}")
    if vital.blood_sugar is not None:
        parts.append(f"혈당 {vital.blood_sugar:g}")
    if vital.heart_rate is not None:
        parts.append(f"심박 {vital.heart_rate}")
    if vital.weight is not None:
        parts.append(f"체중 {vital.weight:g}kg")
    return ", ".join(parts) or vital.notes or "입력된 바이탈 기록"


async def _related_doctor_ids(patient_id: int) -> list[int]:
    record_doctor_ids = await MedicalRecord.filter(patient_id=patient_id).distinct().values_list("doctor_id", flat=True)
    appointment_doctor_ids = await Appointment.filter(patient_id=patient_id).distinct().values_list(
        "doctor_id", flat=True
    )
    return list({*record_doctor_ids, *appointment_doctor_ids})


async def _has_recent_risk_alert(user_id: int, title: str) -> bool:
    since = datetime.now(tz=UTC) - timedelta(hours=24)
    return await Notification.filter(
        user_id=user_id,
        notification_type=NotificationType.HEALTH_RISK_ALERT,
        title=title,
        created_at__gte=since,
    ).exists()


def _format_risk_signal_summary(risk: HealthRiskResponse) -> str:
    if not risk.signals:
        return "세부 신호 없음"
    return ", ".join(f"{signal.label}({signal.detail})" for signal in risk.signals[:3])


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


async def _generate_clinical_note_draft(pre_visit: PreVisitQuestionnaire) -> ClinicalNoteDraftResponse:
    fallback = _fallback_clinical_note_draft(pre_visit)
    prompt = (
        f"주요 증상: {pre_visit.symptoms}\n"
        f"시작 시점: {pre_visit.onset or '미입력'}\n"
        f"심각도: {pre_visit.severity if pre_visit.severity is not None else '미입력'} / 10\n"
        f"복용약: {pre_visit.medications or '미입력'}\n"
        f"과거력: {pre_visit.history or '미입력'}\n"
        f"환자 질문: {pre_visit.questions or '미입력'}\n"
        f"기존 AI 요약: {pre_visit.ai_summary or '없음'}\n\n"
        "아래 JSON 형식만 반환하세요. "
        '{"diagnosis_hint": "...", "symptoms": "...", "soap_note": "...", "follow_up_questions": ["...", "..."]}'
    )
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=_CLINICAL_NOTE_SYSTEM),
            contents=prompt,
        )
        parsed = json.loads((response.text or "").strip().removeprefix("```json").removesuffix("```").strip())
        return ClinicalNoteDraftResponse(
            pre_visit_id=pre_visit.id,
            appointment_id=pre_visit.appointment_id,
            patient_id=pre_visit.patient_id,
            diagnosis_hint=str(parsed.get("diagnosis_hint") or fallback.diagnosis_hint),
            symptoms=str(parsed.get("symptoms") or fallback.symptoms),
            soap_note=str(parsed.get("soap_note") or fallback.soap_note),
            follow_up_questions=[
                str(item) for item in parsed.get("follow_up_questions", fallback.follow_up_questions)
            ][:6],
        )
    except Exception as e:
        logger.warning("Clinical note draft failed: %s", e)
        return fallback


def _fallback_clinical_note_draft(pre_visit: PreVisitQuestionnaire) -> ClinicalNoteDraftResponse:
    follow_up_questions = [
        "증상이 악화되거나 완화되는 상황이 있나요?",
        "동반 증상이나 최근 생활 변화가 있었나요?",
        "복용 중인 약의 효과나 부작용을 느꼈나요?",
    ]
    if pre_visit.questions:
        follow_up_questions.insert(0, f"환자 질문 확인: {pre_visit.questions}")

    soap_note = (
        f"S: {pre_visit.symptoms}\n"
        f"O: 진료 전 문진 기준 심각도 {pre_visit.severity if pre_visit.severity is not None else '미입력'} / 10, "
        f"시작 시점 {pre_visit.onset or '미입력'}.\n"
        f"A: 문진 정보 기반 감별이 필요하며 확정 진단 전 추가 문진과 진찰이 필요합니다.\n"
        f"P: 과거력({pre_visit.history or '미입력'}), 복용약({pre_visit.medications or '미입력'})을 확인하고 "
        "필요 시 검사 및 추적 관찰 계획을 수립합니다."
    )
    return ClinicalNoteDraftResponse(
        pre_visit_id=pre_visit.id,
        appointment_id=pre_visit.appointment_id,
        patient_id=pre_visit.patient_id,
        diagnosis_hint="문진 기반 감별 필요",
        symptoms=pre_visit.symptoms,
        soap_note=soap_note,
        follow_up_questions=follow_up_questions[:6],
    )
