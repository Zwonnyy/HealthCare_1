from celery import Celery
from celery.schedules import crontab

from ai_worker.core import config

celery_app = Celery(
    "ai_worker",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_RESULT_BACKEND,
    include=[
        "ai_worker.tasks.generate_guide",
        "ai_worker.tasks.send_medication_reminder",
        "ai_worker.tasks.analyze_health_logs",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Seoul",
    enable_utc=True,
    beat_schedule={
        "send-medication-reminder-daily": {
            "task": "send_medication_reminder",
            # 매일 오전 8시 (Asia/Seoul)
            "schedule": crontab(hour=8, minute=0),
        },
    },
)
