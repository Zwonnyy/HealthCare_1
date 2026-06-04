import logging

from google import genai
from google.genai import types

from app.core import config
from app.dtos.vitals import VitalCreateRequest
from app.models.users import User
from app.models.vitals import VitalRecord

logger = logging.getLogger(__name__)

_SYSTEM = "당신은 의료 AI 어시스턴트입니다. 환자의 바이탈 수치를 보고 이상 여부를 한국어로 간결하게 안내합니다."

_NORMAL_RANGES = """
혈압: 정상 수축기 90~120mmHg, 이완기 60~80mmHg
혈당: 공복 70~100mg/dL
심박수: 60~100bpm
"""


async def _check_alert(record: VitalRecord) -> str | None:
    parts = []
    if record.systolic is not None:
        parts.append(f"혈압 {record.systolic}/{record.diastolic}mmHg")
    if record.blood_sugar is not None:
        parts.append(f"혈당 {record.blood_sugar}mg/dL")
    if record.weight is not None:
        parts.append(f"체중 {record.weight}kg")
    if record.heart_rate is not None:
        parts.append(f"심박수 {record.heart_rate}bpm")

    if not parts:
        return None

    prompt = (
        f"환자 바이탈: {', '.join(parts)}\n\n"
        f"정상 범위:\n{_NORMAL_RANGES}\n"
        "이상이 있으면 짧게(2문장 이내) 알림 메시지를 작성하세요. "
        "정상 범위라면 '정상 범위입니다.'만 출력하세요."
    )
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        resp = await client.aio.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=_SYSTEM),
            contents=prompt,
        )
        text = (resp.text or "").strip()
        return None if text == "정상 범위입니다." else text
    except Exception as e:
        logger.warning("Vital alert check failed: %s", e)
        return None


class VitalService:
    async def record(self, patient: User, data: VitalCreateRequest) -> VitalRecord:
        vital = await VitalRecord.create(
            patient_id=patient.id,
            systolic=data.systolic,
            diastolic=data.diastolic,
            blood_sugar=data.blood_sugar,
            weight=data.weight,
            heart_rate=data.heart_rate,
            notes=data.notes,
        )
        alert = await _check_alert(vital)
        if alert:
            await VitalRecord.filter(id=vital.id).update(alert_message=alert)
            vital.alert_message = alert
        return vital

    async def list_vitals(self, patient: User, limit: int = 20) -> list[VitalRecord]:
        return await VitalRecord.filter(patient_id=patient.id).order_by("-recorded_at").limit(limit)
