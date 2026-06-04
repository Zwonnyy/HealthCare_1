from fastapi import HTTPException
from google import genai
from google.genai import types
from starlette import status

from app.core import config
from app.models.drug_interactions import DrugInteraction, InteractionStatus
from app.models.records import MedicalRecord
from app.models.users import User, UserRole

_SYSTEM_PROMPT = (
    "당신은 약물 상호작용 전문가 AI입니다. "
    "주어진 처방 약물 목록을 분석하여 위험한 상호작용이 있는지 확인합니다. "
    "모든 답변은 한국어로 작성하며, 의학적으로 정확한 정보를 제공합니다."
)

_USER_PROMPT = """다음 처방 약물들의 상호작용을 분석해주세요.

[처방 약물]
{medications}

다음 형식으로 답변해주세요:

## 상호작용 분석 결과

**위험도**: 안전 / 주의 / 경고 중 하나

각 약물 조합에 대해:
- 상호작용 여부
- 주의사항 또는 경고 내용
- 복약 시 권장 사항

약물이 1개이거나 상호작용이 없으면 "상호작용 없음"으로 답변하세요."""


class DrugInteractionService:
    async def check(self, user: User, record_id: int) -> DrugInteraction:
        record = await MedicalRecord.get_or_none(id=record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        interaction = await DrugInteraction.create(record_id=record_id)
        prescriptions = await record.prescriptions.all()

        if len(prescriptions) < 2:
            await DrugInteraction.filter(id=interaction.id).update(
                status=InteractionStatus.COMPLETED,
                result_text="처방 약물이 1개 이하로 상호작용 분석이 필요하지 않습니다.",
                has_warning=False,
            )
            interaction.status = InteractionStatus.COMPLETED
            interaction.result_text = "처방 약물이 1개 이하로 상호작용 분석이 필요하지 않습니다."
            return interaction

        med_list = "\n".join(
            f"- {p.medication_name} {p.dosage}, {p.frequency}"
            + (f" (특이사항: {p.instructions})" if p.instructions else "")
            for p in prescriptions
        )

        from app.services.rag.drug_rag import search_drug_info

        drug_rag_context = await search_drug_info([p.medication_name for p in prescriptions])
        rag_section = f"\n[참고 약물 정보 (RAG)]\n{drug_rag_context}\n\n" if drug_rag_context else ""
        contents = rag_section + _USER_PROMPT.format(medications=med_list)

        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            response = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
                contents=contents,
            )
            result_text = response.text
            has_warning = any(kw in result_text for kw in ["경고", "위험", "금기", "주의"])
            await DrugInteraction.filter(id=interaction.id).update(
                status=InteractionStatus.COMPLETED,
                result_text=result_text,
                has_warning=has_warning,
            )
            interaction.status = InteractionStatus.COMPLETED
            interaction.result_text = result_text
            interaction.has_warning = has_warning
        except Exception as e:
            await DrugInteraction.filter(id=interaction.id).update(
                status=InteractionStatus.FAILED,
                error_message=str(e),
            )
            interaction.status = InteractionStatus.FAILED

        return interaction

    async def get_latest(self, user: User, record_id: int) -> DrugInteraction | None:
        record = await MedicalRecord.get_or_none(id=record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return await DrugInteraction.filter(record_id=record_id).order_by("-created_at").first()
