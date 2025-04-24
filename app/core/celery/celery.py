from celery import Celery
import os

from app.core.config import REDIS_URL

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")  # ✅ Используем RabbitMQ

celery_app = Celery(
    "app",
    broker=RABBITMQ_URL,  # ✅ Подключаем RabbitMQ
    backend=REDIS_URL,  # ✅ Оставляем Redis для хранения результатов
    include=["app.core.tasks"]
)

celery_app.conf.update(
    task_routes={
        "app.core.tasks.*": {"queue": "default"},
    },
    task_default_queue="default",
    result_expires=3600,
    timezone="UTC"
)
