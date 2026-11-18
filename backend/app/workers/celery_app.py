from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery("vaultly", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.timezone = "UTC"

celery_app.conf.beat_schedule = {
    "evaluate-reminders-every-day": {
        "task": "app.workers.tasks.generate_daily_reminders_task",
        "schedule": crontab(hour=8, minute=0),  # Runs daily at 08:00 UTC
    },
}

celery_app.autodiscover_tasks(["app.workers"])
