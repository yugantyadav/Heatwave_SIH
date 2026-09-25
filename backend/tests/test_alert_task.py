"""Celery alert task: re-alert behaviour.

Regression cover for the old dedup, which keyed on (ward_code, triggered_by)
with no time component: a ward could emit exactly one alert per category for
the lifetime of the database, so a re-escalation days later was dropped.
"""
import asyncio
from datetime import timedelta

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models import Alert, RiskScore
from app.services.alerting import external_id_for, utcnow
from app.tasks.weather_tasks import _trigger_async

WARD = "T-alert-regression"
COOLDOWN_HOURS = 6


async def _seed(category):
    async with AsyncSessionLocal() as s:
        s.add(RiskScore(ward_code=WARD, risk_category=category, final_score=80.0,
                        created_at=utcnow()))
        await s.commit()


async def _move_alerts_into_past_window():
    """Age existing alerts so they belong to an already-elapsed window."""
    old = utcnow() - timedelta(hours=COOLDOWN_HOURS + 1)
    async with AsyncSessionLocal() as s:
        for a in (await s.execute(select(Alert).where(Alert.ward_code == WARD))).scalars().all():
            a.sent_at = old
            a.external_id = external_id_for("celery", WARD, a.triggered_by, old, COOLDOWN_HOURS * 3600)
        await s.commit()


async def _cleanup():
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Alert).where(Alert.ward_code == WARD))
        await s.execute(delete(RiskScore).where(RiskScore.ward_code == WARD))
        await s.commit()


def _alerts():
    async def run():
        async with AsyncSessionLocal() as s:
            return (await s.execute(
                select(Alert).where(Alert.ward_code == WARD)
            )).scalars().all()

    return asyncio.run(run())


def _run_task():
    return asyncio.run(_trigger_async())


def test_realert_after_cooldown(client):
    asyncio.run(_cleanup())
    try:
        asyncio.run(_seed("HIGH"))
        assert _run_task()["created"] == 1

        # Re-running inside the same window must not add a second alert.
        assert _run_task()["created"] == 0
        assert len(_alerts()) == 1

        # Once the window has elapsed the ward is allowed to alert again.
        asyncio.run(_move_alerts_into_past_window())
        assert _run_task()["created"] == 1
        assert len(_alerts()) == 2
    finally:
        asyncio.run(_cleanup())


def test_low_risk_wards_never_alert(client):
    asyncio.run(_cleanup())
    try:
        asyncio.run(_seed("LOW"))
        assert _run_task()["created"] == 0
        assert _alerts() == []
    finally:
        asyncio.run(_cleanup())
