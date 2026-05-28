from fastapi import HTTPException
from starlette import status

from app.core.celery import celery_client
from app.dtos.health_logs import HealthLogCreateRequest
from app.models.health_logs import HealthLog, HealthLogAnalysis
from app.models.users import User, UserRole
from app.repositories.health_log_repository import HealthLogRepository
from app.repositories.record_repository import RecordRepository


class HealthLogService:
    def __init__(self):
        self.log_repo = HealthLogRepository()
        self.record_repo = RecordRepository()

    async def create_log(self, user: User, data: HealthLogCreateRequest) -> HealthLog:
        if data.record_id:
            record = await self.record_repo.get_record(data.record_id)
            if not record:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
            if record.patient_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        return await self.log_repo.create_log(
            patient_id=user.id,
            record_id=data.record_id,
            log_date=data.log_date,
            pain_score=data.pain_score,
            mood=data.mood,
            symptoms_text=data.symptoms_text,
            notes=data.notes,
        )

    async def get_my_logs(self, user: User, offset: int = 0, limit: int = 20) -> tuple[list[HealthLog], int]:
        items = await self.log_repo.get_patient_logs(user.id, offset=offset, limit=limit)
        total = await self.log_repo.count_patient_logs(user.id)
        return items, total

    async def get_log(self, user: User, log_id: int) -> HealthLog:
        log = await self.log_repo.get_log(log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="건강 일지를 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and log.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR:
            # 의사는 자신이 담당한 진료 기록에 연결된 일지만 조회 가능
            if not log.record_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
            record = await self.record_repo.get_record(log.record_id)
            if not record or record.doctor_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return log

    async def get_record_logs(self, user: User, record_id: int) -> list[HealthLog]:
        record = await self.record_repo.get_record(record_id)
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
        if user.role == UserRole.PATIENT and record.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        if user.role == UserRole.DOCTOR and record.doctor_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return await self.log_repo.get_record_logs(record_id)

    async def delete_log(self, user: User, log_id: int) -> None:
        log = await self.log_repo.get_log(log_id)
        if not log:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="건강 일지를 찾을 수 없습니다.")
        if log.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        await self.log_repo.delete_log(log_id)

    async def request_analysis(self, user: User, record_id: int | None) -> HealthLogAnalysis:
        if record_id:
            record = await self.record_repo.get_record(record_id)
            if not record:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료 기록을 찾을 수 없습니다.")
            if record.patient_id != user.id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

        logs = (
            await self.log_repo.get_record_logs(record_id)
            if record_id
            else await self.log_repo.get_patient_logs(user.id, limit=10000)
        )
        if not logs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="분석할 건강 일지가 없습니다.")

        analysis = await self.log_repo.create_analysis(patient_id=user.id, record_id=record_id)
        celery_client.send_task("analyze_health_logs", args=[analysis.id])
        return analysis

    async def get_analysis(self, user: User, analysis_id: int) -> HealthLogAnalysis:
        analysis = await self.log_repo.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="분석 결과를 찾을 수 없습니다.")
        if analysis.patient_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")
        return analysis
