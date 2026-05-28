import asyncio

from celery import shared_task
from google import genai
from google.genai import types
from tortoise import Tortoise

from ai_worker.core import config
from ai_worker.core.databases import TORTOISE_ORM

GUIDE_SYSTEM_PROMPT = (
    "당신은 전문 의료 정보 AI 어시스턴트입니다. 환자의 진료 기록을 바탕으로 "
    "정확하고 이해하기 쉬운 복약 안내와 생활습관 개선 가이드를 제공합니다. "
    "모든 내용은 한국어로 작성하며, 환자가 쉽게 이해할 수 있도록 친근하게 설명합니다.\n"
    "※ 이 가이드는 참고 정보이며, 실제 의료 결정은 담당 의사와 상담하시기 바랍니다."
)

GUIDE_USER_PROMPT_TEMPLATE = """다음 진료 기록을 바탕으로 가이드를 작성해주세요.

[진료 정보]
- 진단명: {diagnosis}
- 주요 증상: {symptoms}
- 의사 메모: {notes}

[처방 약물]
{prescriptions_text}

다음 형식으로 작성해주세요:

## 1. 복약 안내
각 약물별로 복용 방법, 복용 시간, 주의사항, 흔한 부작용을 설명해주세요.

## 2. 생활습관 개선 가이드
식단 관리, 운동 권장사항, 수면 및 휴식, 피해야 할 것들, 기타 생활 습관 조언을 작성해주세요."""


@shared_task(name="generate_guide")
def generate_guide_task(guide_id: int) -> None:
    asyncio.run(_generate_guide(guide_id))


async def _generate_guide(guide_id: int) -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        from app.models.guides import Guide, GuideStatus

        guide = await Guide.get_or_none(id=guide_id)
        if not guide:
            return

        await Guide.filter(id=guide_id).update(status=GuideStatus.GENERATING)

        record = await guide.record
        prescriptions = await record.prescriptions.all()

        prescriptions_text = "\n".join(
            f"- {p.medication_name} {p.dosage}, {p.frequency}, {p.duration_days}일 복용"
            + (f" (특이사항: {p.instructions})" if p.instructions else "")
            for p in prescriptions
        )
        if not prescriptions_text:
            prescriptions_text = "처방 약물 없음"

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(
                system_instruction=GUIDE_SYSTEM_PROMPT,
            ),
            contents=GUIDE_USER_PROMPT_TEMPLATE.format(
                diagnosis=record.diagnosis,
                symptoms=record.symptoms,
                notes=record.notes or "없음",
                prescriptions_text=prescriptions_text,
            ),
        )

        full_text = response.text

        if "## 2." in full_text:
            parts = full_text.split("## 2.")
            medication_guide = parts[0].replace("## 1.", "").strip()
            lifestyle_guide = parts[1].strip()
        else:
            medication_guide = full_text
            lifestyle_guide = None

        await Guide.filter(id=guide_id).update(
            status=GuideStatus.COMPLETED,
            medication_guide=medication_guide,
            lifestyle_guide=lifestyle_guide,
        )

    except Exception as e:
        await Guide.filter(id=guide_id).update(
            status=GuideStatus.FAILED,
            error_message=str(e),
        )
    finally:
        await Tortoise.close_connections()
