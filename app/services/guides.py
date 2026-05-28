import json
from asyncio import CancelledError
from collections.abc import AsyncGenerator

from fastapi import HTTPException
from google import genai
from google.genai import types
from starlette import status

from app.core import config
from app.core.celery import celery_client
from app.models.guides import Guide, GuideStatus
from app.models.users import User, UserRole
from app.repositories.guide_repository import GuideRepository
from app.repositories.record_repository import RecordRepository

_GUIDE_SYSTEM_PROMPT = (
    "당신은 전문 의료 정보 AI 어시스턴트입니다. 환자의 진료 기록을 바탕으로 "
    "정확하고 이해하기 쉬운 복약 안내와 생활습관 개선 가이드를 제공합니다. "
    "모든 내용은 한국어로 작성하며, 환자가 쉽게 이해할 수 있도록 친근하게 설명합니다.\n"
    "※ 이 가이드는 참고 정보이며, 실제 의료 결정은 담당 의사와 상담하시기 바랍니다."
)

_GUIDE_USER_PROMPT_TEMPLATE = """다음 진료 기록을 바탕으로 가이드를 작성해주세요.

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


class GuideService:
    def __init__(self):
        self.guide_repo = GuideRepository()
        self.record_repo = RecordRepository()

    async def request_guide(self, user: User, record_id: int) -> Guide:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        guide = await self.guide_repo.create_guide(record_id=record_id)
        celery_client.send_task("generate_guide", args=[guide.id])
        return guide

    async def get_guide(self, user: User, guide_id: int) -> Guide:
        guide = await self.guide_repo.get_guide(guide_id)
        if not guide:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="가이드를 찾을 수 없습니다.")
        record = await self.record_repo.get_record(guide.record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return guide

    async def get_record_guides(self, user: User, record_id: int) -> list[Guide]:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return await self.guide_repo.get_record_guides(record_id)

    async def stream_guide(self, user: User, record_id: int) -> AsyncGenerator[str, None]:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        prescriptions = await record.prescriptions.all()
        prescriptions_text = (
            "\n".join(
                f"- {p.medication_name} {p.dosage}, {p.frequency}, {p.duration_days}일 복용"
                + (f" (특이사항: {p.instructions})" if p.instructions else "")
                for p in prescriptions
            )
            or "처방 약물 없음"
        )

        guide = await self.guide_repo.create_guide(record_id=record_id)
        await Guide.filter(id=guide.id).update(status=GuideStatus.GENERATING)

        return _generate_guide_stream(
            guide_id=guide.id,
            diagnosis=record.diagnosis,
            symptoms=record.symptoms,
            notes=record.notes,
            prescriptions_text=prescriptions_text,
        )


async def _generate_guide_stream(
    guide_id: int,
    diagnosis: str,
    symptoms: str,
    prescriptions_text: str,
    notes: str | None,
) -> AsyncGenerator[str, None]:
    full_text = ""
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        async for chunk in await client.aio.models.generate_content_stream(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=_GUIDE_SYSTEM_PROMPT),
            contents=_GUIDE_USER_PROMPT_TEMPLATE.format(
                diagnosis=diagnosis,
                symptoms=symptoms,
                notes=notes or "없음",
                prescriptions_text=prescriptions_text,
            ),
        ):
            if chunk.text:
                full_text += chunk.text
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk.text}, ensure_ascii=False)}\n\n"

        # 파싱 후 DB 저장
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
        yield f"data: {json.dumps({'type': 'done', 'guide_id': guide_id}, ensure_ascii=False)}\n\n"

    except CancelledError:
        # 클라이언트 연결 끊김 — 생성된 내용이 있으면 부분 저장
        if full_text:
            await Guide.filter(id=guide_id).update(
                status=GuideStatus.COMPLETED,
                medication_guide=full_text,
            )
        else:
            await Guide.filter(id=guide_id).update(status=GuideStatus.FAILED, error_message="연결이 끊겼습니다.")

    except Exception as e:
        await Guide.filter(id=guide_id).update(status=GuideStatus.FAILED, error_message=str(e))
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
