import asyncio

from celery import shared_task
from google import genai
from google.genai import types
from tortoise import Tortoise

from ai_worker.core import config
from ai_worker.core.databases import TORTOISE_ORM

ANALYSIS_SYSTEM_PROMPT = (
    "당신은 전문 의료 정보 AI 어시스턴트입니다. 환자의 건강 일지를 분석하여 "
    "회복 추이와 건강 상태 변화를 평가하고, 환자가 이해하기 쉬운 피드백을 제공합니다. "
    "모든 내용은 한국어로 작성하며, 환자가 쉽게 이해할 수 있도록 친근하게 설명합니다.\n"
    "※ 이 분석은 참고 정보이며, 실제 의료 결정은 담당 의사와 상담하시기 바랍니다."
)

ANALYSIS_USER_PROMPT_TEMPLATE = """다음은 환자의 건강 일지 기록입니다. 회복 추이를 분석해주세요.

{record_info}

[건강 일지 기록]
{logs_text}

다음 형식으로 작성해주세요:

## 1. 전반적인 회복 추이
날짜별 통증 수치와 기분 변화를 바탕으로 전반적인 회복 흐름을 평가해주세요.

## 2. 증상 변화 분석
주요 증상의 개선 또는 악화 여부를 분석해주세요.

## 3. 권장 사항
현재 상태를 바탕으로 환자에게 도움이 될 조언을 제공해주세요."""


@shared_task(name="analyze_health_logs")
def analyze_health_logs_task(analysis_id: int) -> None:
    asyncio.run(_analyze_health_logs(analysis_id))


async def _analyze_health_logs(analysis_id: int) -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        from app.models.health_logs import AnalysisStatus, HealthLog, HealthLogAnalysis
        from app.models.records import MedicalRecord

        analysis = await HealthLogAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return

        await HealthLogAnalysis.filter(id=analysis_id).update(status=AnalysisStatus.GENERATING)

        # 일지 조회
        if analysis.record_id:
            logs = await HealthLog.filter(record_id=analysis.record_id).order_by("log_date")
        else:
            logs = await HealthLog.filter(patient_id=analysis.patient_id).order_by("log_date")

        if not logs:
            await HealthLogAnalysis.filter(id=analysis_id).update(
                status=AnalysisStatus.FAILED,
                error_message="분석할 건강 일지가 없습니다.",
            )
            return

        # 진료 기록 정보 (있는 경우)
        record_info = ""
        if analysis.record_id:
            record = await MedicalRecord.get_or_none(id=analysis.record_id)
            if record:
                record_info = (
                    f"[연관 진료 기록]\n"
                    f"- 진단명: {record.diagnosis}\n"
                    f"- 주요 증상: {record.symptoms}\n"
                    f"- 진료일: {record.visited_at.strftime('%Y-%m-%d')}\n"
                )

        mood_labels = {"GREAT": "매우 좋음", "GOOD": "좋음", "NORMAL": "보통", "BAD": "나쁨", "TERRIBLE": "매우 나쁨"}
        logs_text = "\n".join(
            f"- [{log.log_date}] 통증: {log.pain_score}/10, 기분: {mood_labels.get(log.mood, log.mood)}, "
            f"증상: {log.symptoms_text}" + (f", 메모: {log.notes}" if log.notes else "")
            for log in logs
        )

        client = genai.Client(api_key=config.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            config=types.GenerateContentConfig(system_instruction=ANALYSIS_SYSTEM_PROMPT),
            contents=ANALYSIS_USER_PROMPT_TEMPLATE.format(
                record_info=record_info,
                logs_text=logs_text,
            ),
        )

        await HealthLogAnalysis.filter(id=analysis_id).update(
            status=AnalysisStatus.COMPLETED,
            analysis_text=response.text,
        )

    except Exception as e:
        await HealthLogAnalysis.filter(id=analysis_id).update(
            status=AnalysisStatus.FAILED,
            error_message=str(e),
        )
    finally:
        await Tortoise.close_connections()
