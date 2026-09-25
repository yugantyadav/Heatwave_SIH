from celery import Celery
from celery.schedules import schedule
from celery.signals import worker_ready
from app.core.config import settings

celery_app = Celery(
    "heatwave_ews",
    # Previously hardcoded to localhost, which silently ignored the REDIS_URL
    # that every deploy config sets — the worker could never reach the broker.
    broker=settings.REDIS_URL,
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
    # refresh/compute/trigger run as one ordered pipeline. Scheduling them as
    # three independent entries at the same period meant they fired at the same
    # instant, so compute could score the previous refresh's weather.
    beat_schedule={
        "refresh-compute-trigger": {
            "task": "tasks.weather_tasks.pipeline",
            "schedule": schedule(run_every=REFRESH_SECS),
        },
        "check-alerts": {
            "task": "tasks.alert_tasks.trigger",
            "schedule": schedule(run_every=3600),
        },
    },
)


@worker_ready.connect
def _run_pipeline_on_boot(**_kwargs):
    """Celery's run_every is a *delay*, so on a cold start nothing ran for a
    full refresh period. Kick the pipeline once as soon as the worker is up."""
    celery_app.send_task("tasks.weather_tasks.pipeline")


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
