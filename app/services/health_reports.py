from datetime import date

from google import genai
from google.genai import types

from app.core import config
from app.models.health_goals import HealthGoal
from app.models.health_logs import HealthLog
from app.models.health_reports import HealthReport, ReportStatus
from app.models.users import User

_SYSTEM_PROMPT = (
    "당신은 환자의 월별 건강 데이터를 분석하는 AI 건강 코치입니다. "
    "데이터를 기반으로 친절하고 전문적인 월별 건강 리포트를 한국어로 작성합니다."
)


class HealthReportService:
    async def generate(self, patient: User, year: int, month: int) -> HealthReport:
        existing = await HealthReport.filter(patient_id=patient.id, year=year, month=month).first()
        if existing and existing.status == ReportStatus.COMPLETED:
            return existing

        report = existing or await HealthReport.create(patient_id=patient.id, year=year, month=month)

        from_date = date(year, month, 1)
        to_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)

        health_logs = await HealthLog.filter(
            patient_id=patient.id, log_date__gte=from_date, log_date__lt=to_date
        ).order_by("log_date")
        goals = await HealthGoal.filter(patient_id=patient.id)

        if health_logs:
            avg_pain = sum(log.pain_score for log in health_logs) / len(health_logs)
            mood_counts: dict[str, int] = {}
            for log in health_logs:
                mood_counts[str(log.mood)] = mood_counts.get(str(log.mood), 0) + 1
            logs_summary = (
                f"건강 일지 기록: {len(health_logs)}건\n"
                f"평균 통증 점수: {avg_pain:.1f}/10\n"
                f"기분 분포: {', '.join(f'{k} {v}회' for k, v in mood_counts.items())}"
            )
        else:
            logs_summary = "이 달에 기록된 건강 일지가 없습니다."

        if goals:
            goals_summary = "건강 목표:\n" + "\n".join(
                f"- {g.title}: 목표 {g.target_value}{g.unit}, "
                f"현재 {g.current_value if g.current_value is not None else '미입력'}{g.unit}, "
                f"{'달성완료' if g.achieved else '진행 중'}"
                for g in goals
            )
        else:
            goals_summary = "설정된 건강 목표가 없습니다."

        from app.services.rag.guideline_rag import search_guidelines

        guideline_context = await search_guidelines(query=f"건강 관리 {logs_summary[:100]}")
        guideline_section = f"\n[관련 의학 가이드라인]\n{guideline_context}\n" if guideline_context else ""

        prompt = f"""{year}년 {month}월 건강 리포트를 작성해주세요.
{guideline_section}
[이달의 건강 데이터]
{logs_summary}

[건강 목표 현황]
{goals_summary}

다음 형식으로 작성해주세요:

## {year}년 {month}월 건강 리포트

### 이달의 건강 요약
(전반적인 건강 상태를 2-3문장으로 평가)

### 통증 및 컨디션 분석
(통증 점수와 기분 데이터 기반 분석)

### 목표 달성 현황
(건강 목표 진행 상황 평가)

### 다음 달 권장 사항
(구체적인 개선 방안 3가지)"""

        try:
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            response = await client.aio.models.generate_content(
                model="gemini-flash-latest",
                config=types.GenerateContentConfig(system_instruction=_SYSTEM_PROMPT),
                contents=prompt,
            )
            await HealthReport.filter(id=report.id).update(
                status=ReportStatus.COMPLETED,
                report_text=response.text,
            )
            report.status = ReportStatus.COMPLETED
            report.report_text = response.text
        except Exception as e:
            await HealthReport.filter(id=report.id).update(
                status=ReportStatus.FAILED,
                error_message=str(e),
            )
            report.status = ReportStatus.FAILED

        return report

    async def list_reports(self, patient: User) -> list[HealthReport]:
        return await HealthReport.filter(patient_id=patient.id).order_by("-year", "-month")
