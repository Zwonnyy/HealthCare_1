from celery import Celery

from app.core import config

celery_client = Celery(broker=config.CELERY_BROKER_URL)