import json
import logging

from google import genai
from google.genai import types

from app.core import config
from app.models.symptom_checks import SymptomCheck, UrgencyLevel
from app.models.users import User

logger = logging.getLogger(__name__)

_SYSTEM = (
    "당신은 1차 의료 AI 트리아지 어시스턴트입니다. "
    "환자의 증상을 듣고 긴급도를 평가하고 진료 권고를 한국어로 제공합니다. "
    "응답은 반드시 JSON 형식으로만 반환하세요."
)

_PROMPT_TMPL = """{guideline_section}환자 증상: {symptom_text}

다음 JSON 형식으로만 응답하세요:
{{
  "urgency": "LOW|MEDIUM|HIGH",
  "assessment": "증상 평가 내용 (3-4문장)",
  "recommendation": "권고 사항 (2-3가지)",
  "suggest_appointment": true|false
}}

urgency 기준:
- HIGH: 즉시 응급실 필요 (흉통, 호흡 곤란, 의식 변화 등)
- MEDIUM: 48시간 내 진료 권고
- LOW: 가정 요법으로 충분하나 지속 시 진료 권고"""


async def search_guidelines(query: str, limit: int = 2) -> str:
    from app.services.rag.guideline_rag import search_guidelines as rag_search_guidelines

    return await rag_search_guidelines(query=query, limit=limit)


class SymptomCheckService:
    async def check(self, patient: User, symptom_text: str) -> SymptomCheck:
        guideline_context = await search_guidelines(query=symptom_text, limit=2)
        guideline_section = f"[관련 의학 가이드라인]\n{guideline_context}\n\n" if guideline_context else ""

        prompt = _PROMPT_TMPL.format(
            guideline_section=guideline_section,
            symptom_text=symptom_text,
        )

        assessment = None
        urgency = None
        suggest = False

        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            resp = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM,
                    response_mime_type="application/json",
                ),
                contents=prompt,
            )
            data = json.loads(resp.text or "{}")
            raw_urgency = data.get("urgency", "LOW").upper()
            urgency = UrgencyLevel(raw_urgency) if raw_urgency in UrgencyLevel._value2member_map_ else UrgencyLevel.LOW
            assessment_text = data.get("assessment", "")
            recommendation = data.get("recommendation", "")
            assessment = f"{assessment_text}\n\n권고 사항: {recommendation}" if recommendation else assessment_text
            suggest = bool(data.get("suggest_appointment", False))
        except Exception as e:
            logger.warning("Symptom check AI failed: %s", e)
            assessment = "AI 분석 중 오류가 발생했습니다. 증상이 심각하다면 즉시 진료를 받으세요."

        return await SymptomCheck.create(
            patient_id=patient.id,
            symptom_text=symptom_text,
            ai_assessment=assessment,
            urgency=urgency,
            suggest_appointment=suggest,
        )

    async def list_checks(self, patient: User, limit: int = 10) -> list[SymptomCheck]:
        return await SymptomCheck.filter(patient_id=patient.id).order_by("-created_at").limit(limit)
