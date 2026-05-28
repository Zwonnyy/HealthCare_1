import asyncio
import logging
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

import aiosmtplib
from celery import shared_task
from tortoise import Tortoise

from ai_worker.core import config
from ai_worker.core.databases import TORTOISE_ORM

if TYPE_CHECKING:
    from app.models.records import Prescription
    from app.models.users import User

logger = logging.getLogger(__name__)


@shared_task(name="send_medication_reminder")
def send_medication_reminder_task() -> None:
    asyncio.run(_send_medication_reminders())


async def _send_medication_reminders() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        from app.models.records import Prescription
        from app.models.users import User

        today = date.today()

        # 오늘 기준으로 복약 중인 처방전이 있는 진료 기록 조회
        # visited_at.date() + duration_days >= today 인 처방전
        all_prescriptions = await Prescription.all().prefetch_related("record__patient")

        # 환자별 복약 중인 처방전 그룹핑
        patient_prescriptions: dict[int, tuple[User, list[Prescription]]] = {}
        for prescription in all_prescriptions:
            record = await prescription.record
            end_date = record.visited_at.date() + timedelta(days=prescription.duration_days)
            if record.visited_at.date() <= today <= end_date:
                patient = await record.patient
                if patient.id not in patient_prescriptions:
                    patient_prescriptions[patient.id] = (patient, [])
                patient_prescriptions[patient.id][1].append(prescription)

        if not patient_prescriptions:
            logger.info("복약 중인 환자가 없습니다.")
            return

        sent_count = 0
        for patient_id, (patient, prescriptions) in patient_prescriptions.items():
            try:
                await _send_reminder_email(patient=patient, prescriptions=prescriptions)
                sent_count += 1
                logger.info("복약 알림 발송 완료: %s (%s)", patient.name, patient.email)
            except Exception as e:
                logger.error("복약 알림 발송 실패 [patient_id=%s]: %s", patient_id, e)

        logger.info("복약 알림 발송 완료: %d명", sent_count)

    finally:
        await Tortoise.close_connections()


async def _send_reminder_email(patient: "User", prescriptions: list["Prescription"]) -> None:
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        logger.warning("SMTP 설정이 없어 이메일 발송을 건너뜁니다.")
        return

    html_body = _build_email_html(patient_name=patient.name, prescriptions=prescriptions)

    message = MIMEMultipart("alternative")
    message["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_USER}>"
    message["To"] = patient.email
    message["Subject"] = f"[AI Health] {patient.name}님, 오늘 복약을 잊지 마세요!"
    message.attach(MIMEText(html_body, "html", "utf-8"))

    await aiosmtplib.send(
        message,
        hostname=config.SMTP_HOST,
        port=config.SMTP_PORT,
        username=config.SMTP_USER,
        password=config.SMTP_PASSWORD,
        start_tls=True,
    )


def _build_email_html(patient_name: str, prescriptions: list["Prescription"]) -> str:
    prescription_rows = ""
    for p in prescriptions:
        instructions_html = f"<br><small style='color:#888;'>{p.instructions}</small>" if p.instructions else ""
        prescription_rows += f"""
        <tr>
            <td style="padding:12px;border-bottom:1px solid #eee;">
                <strong>{p.medication_name}</strong>{instructions_html}
            </td>
            <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;">{p.dosage}</td>
            <td style="padding:12px;border-bottom:1px solid #eee;text-align:center;">{p.frequency}</td>
        </tr>"""

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f5f5f5;font-family:'Apple SD Gothic Neo',Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:40px 0;">
            <tr><td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background:#4A90D9;padding:32px 40px;text-align:center;">
                            <h1 style="color:#fff;margin:0;font-size:24px;">💊 오늘의 복약 안내</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:32px 40px;">
                            <p style="font-size:16px;color:#333;margin:0 0 24px;">
                                안녕하세요, <strong>{patient_name}</strong>님!<br>
                                오늘 복용하셔야 할 약물을 안내해 드립니다.
                            </p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #eee;border-radius:8px;overflow:hidden;">
                                <thead>
                                    <tr style="background:#f8f9fa;">
                                        <th style="padding:12px;text-align:left;color:#666;font-size:13px;">약물명</th>
                                        <th style="padding:12px;text-align:center;color:#666;font-size:13px;">용량</th>
                                        <th style="padding:12px;text-align:center;color:#666;font-size:13px;">복용 방법</th>
                                    </tr>
                                </thead>
                                <tbody>{prescription_rows}</tbody>
                            </table>
                            <p style="font-size:13px;color:#999;margin:24px 0 0;padding:16px;background:#fff9e6;border-radius:8px;border-left:4px solid #ffc107;">
                                ⚠️ 이 알림은 참고용이며, 복약 관련 문의는 담당 의사 또는 약사에게 상담하세요.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f8f9fa;padding:20px 40px;text-align:center;">
                            <p style="color:#999;font-size:12px;margin:0;">AI Health &copy; 2026</p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>"""
