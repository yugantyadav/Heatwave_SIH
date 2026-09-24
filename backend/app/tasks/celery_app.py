from celery import Celery
from celery.schedules import schedule
from app.core.config import settings

celery_app = Celery(
    "heatwave_ews",
    broker="redis://localhost:6379/0",
    backend="rpc://",
    include=["app.tasks.weather_tasks"],
)

REFRESH_SECS = int(settings.FORECAST_REFRESH_HOURS) * 3600

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "refresh-forecast": {
            "task": "tasks.weather_tasks.refresh",
            "schedule": schedule(run_every=REFRESH_SECS),
        },
        "compute-risk": {
            "task": "tasks.risk_tasks.compute",
            "schedule": schedule(run_every=REFRESH_SECS),
        },
        "check-alerts": {
            "task": "tasks.alert_tasks.trigger",
            "schedule": schedule(run_every=3600),
        },
    },
)

@celery_app.task(name="tasks.refresh_forecast")
def refresh_forecast():
    from app.tasks.weather_tasks import refresh as _refresh
    return _refresh()

@celery_app.task(name="tasks.compute_risk_scores")
def compute_risk_scores():
    from app.tasks.weather_tasks import compute as _compute
    return _compute()

@celery_app.task(name="tasks.trigger_alerts")
def trigger_alerts():
    from app.tasks.weather_tasks import trigger as _trigger
    return _trigger()
