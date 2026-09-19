from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "heatwave_ews",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.weather_tasks", "app.tasks.risk_tasks", "app.tasks.alert_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

@celery_app.task
def refresh_forecast():
    return {"status": "forecast refresh triggered"}

@celery_app.task
def compute_risk_scores():
    return {"status": "risk computation triggered"}

@celery_app.task
def trigger_alerts():
    return {"status": "alert trigger checked"}