import asyncio
import logging

from celery import shared_task
from tortoise import Tortoise

from ai_worker.core import config
from ai_worker.core.databases import TORTOISE_ORM

logger = logging.getLogger(__name__)


@shared_task(name="check_medication_reminders")
def check_medication_reminders_task() -> None:
    asyncio.run(_check_reminders())


async def _check_reminders() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        from app.services.medication_reminders import send_due_reminders

        count = await send_due_reminders()
        if count:
            logger.info("복약 알림 발송: %d건", count)
    except Exception as e:
        logger.error("복약 알림 체크 실패: %s", e)
    finally:
        await Tortoise.close_connections()
