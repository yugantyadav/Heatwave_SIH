from app.tasks.celery_app import celery_app

@celery_app.task(name="tasks.weather_tasks.refresh")
def refresh():
    return {"status": "weather forecast refreshed"}

@celery_app.task(name="tasks.risk_tasks.compute")
def compute():
    return {"status": "risk scores computed"}

@celery_app.task(name="tasks.alert_tasks.trigger")
def trigger():
    return {"status": "alerts triggered"}