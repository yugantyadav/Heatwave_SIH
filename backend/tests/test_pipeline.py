"""The scheduled pipeline must run refresh -> compute -> trigger in order.

Scheduling the three jobs independently at the same period let compute read
the *previous* refresh's weather, because they fired at the same instant.
"""
import pytest

from app.tasks import weather_tasks


def test_pipeline_runs_steps_in_order(monkeypatch, client):
    order = []

    async def fake_refresh():
        order.append("refresh")
        return {"status": "ok"}

    async def fake_compute():
        order.append("compute")
        return {"status": "ok"}

    async def fake_trigger():
        order.append("trigger")
        return {"status": "ok"}

    monkeypatch.setattr(weather_tasks, "_refresh_async", fake_refresh)
    monkeypatch.setattr(weather_tasks, "_compute_async", fake_compute)
    monkeypatch.setattr(weather_tasks, "_trigger_async", fake_trigger)

    out = pytest.importorskip("asyncio").run(weather_tasks._pipeline_async())

    assert order == ["refresh", "compute", "trigger"]
    assert out["refresh"]["status"] == "ok"
    assert out["compute"]["status"] == "ok"
    assert out["trigger"]["status"] == "ok"


def test_pipeline_isolates_a_failing_step(monkeypatch, client):
    """A dead Open-Meteo must not stop risk being computed or alerts checked."""
    import asyncio

    order = []

    async def boom():
        order.append("refresh")
        raise RuntimeError("upstream down")

    async def fake_compute():
        order.append("compute")
        return {"status": "ok"}

    async def fake_trigger():
        order.append("trigger")
        return {"status": "ok"}

    monkeypatch.setattr(weather_tasks, "_refresh_async", boom)
    monkeypatch.setattr(weather_tasks, "_compute_async", fake_compute)
    monkeypatch.setattr(weather_tasks, "_trigger_async", fake_trigger)

    out = asyncio.run(weather_tasks._pipeline_async())

    assert order == ["refresh", "compute", "trigger"]
    assert out["refresh"]["status"] == "failed"
    assert "upstream down" in out["refresh"]["error"]
    assert out["compute"]["status"] == "ok"
    assert out["trigger"]["status"] == "ok"


def test_beat_schedule_uses_single_ordered_pipeline():
    """No two independent jobs may share one period."""
    from datetime import timedelta

    from app.tasks.celery_app import REFRESH_SECS, celery_app

    schedule = celery_app.conf.beat_schedule
    assert "refresh-compute-trigger" in schedule
    assert schedule["refresh-compute-trigger"]["task"] == "tasks.weather_tasks.pipeline"
    assert schedule["refresh-compute-trigger"]["schedule"].run_every == timedelta(seconds=REFRESH_SECS)

    # the old per-job entries must be gone
    assert "refresh-forecast" not in schedule
    assert "compute-risk" not in schedule


def test_broker_comes_from_settings(monkeypatch):
    """Broker used to be hardcoded to localhost, ignoring REDIS_URL."""
    from app.core.config import settings
    from app.tasks.celery_app import celery_app

    assert celery_app.conf.broker_url == settings.REDIS_URL
    assert settings.REDIS_URL
