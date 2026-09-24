"""Scheduled jobs: forecast refresh (6h) -> risk computation -> alert check.

Each task is idempotent and safe to run manually:
    celery -A app.tasks.celery_app worker --loglevel=info
    celery -A app.tasks.celery_app beat --loglevel=info

Uses synchronous SQLite (Celery worker process), no async engine needed.
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager

import aiohttp
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.db.session import Base, AsyncSessionLocal
from app.models import AdvisoryTemplate, Alert, RiskScore, Ward, WeatherReading
from app.services.risk_model import MortalityRiskService
from app.services.thermal_index import ThermalIndexService
from app.tasks.celery_app import celery_app

MUMBAI_LAT, MUMBAI_LON = 19.076, 72.8777

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "heatwave.db"))


def _engine():
    return create_async_engine(settings.DATABASE_URL, echo=False)


async def _refresh_async():
    engine = _engine()
    params = {
        "latitude": MUMBAI_LAT,
        "longitude": MUMBAI_LON,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode",
        "timezone": "Asia/Kolkata",
        "forecast_days": 5,
    }
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20) as resp:
                data = await resp.json()
        hourly = data.get("hourly", {})
        idx = -1
        t = float(hourly["temperature_2m"][idx])
        rh = float(hourly["relative_humidity_2m"][idx])
        pr = float(hourly.get("precipitation", [0])[-1])
        wc = int(hourly.get("weathercode", [0])[-1])
        source = "open-meteo"
    except Exception:
        fc_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mumbai_weather_forecast.json"))
        with open(fc_path) as f:
            fc = json.load(f)
        h = fc["hourly"]
        t = float(h["temperature_2m"][-1])
        rh = float(h["relative_humidity_2m"][-1])
        pr = float(h["precipitation"][-1])
        wc = int(h["weathercode"][-1])
        source = "bundled-fallback"
    th = ThermalIndexService.calculate(t, rh)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        wards = (await session.execute(select(Ward))).scalars().all()
        for w in wards:
            session.add(WeatherReading(
                ward_code=w.ward_code, temperature_2m=t,
                relative_humidity_2m=rh, precipitation=pr, weathercode=wc,
                heat_index=th.get("heat_index"), wbgt=th.get("wbgt"),
            ))
        await session.commit()
        n = len(wards)
    await engine.dispose()
    return {"status": "weather forecast refreshed", "wards": n, "source": source,
            "temperature_2m": t, "heat_index": th.get("heat_index"), "wbgt": th.get("wbgt")}


async def _compute_async():
    engine = _engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        wards = (await session.execute(select(Ward))).scalars().all()
        n = 0
        for w in wards:
            wr = (await session.execute(
                select(WeatherReading).where(WeatherReading.ward_code == w.ward_code)
                .order_by(desc(WeatherReading.recorded_at)).limit(1))).scalar_one_or_none()
            if not wr:
                continue
            risk = MortalityRiskService.calculate_risk(
                heat_index=wr.heat_index or 35.0, wbgt=wr.wbgt or 28.0,
                elderly_percent=w.elderly_percent or 8.57,
                outdoor_worker_density=w.outdoor_worker_density or 0.5,
                temperature_c=wr.temperature_2m, humidity=wr.relative_humidity_2m,
            )
            session.add(RiskScore(
                ward_code=w.ward_code, risk_category=str(risk["risk_category"]).upper(),
                final_score=risk["final_score"], heat_index=wr.heat_index, wbgt=wr.wbgt,
                elderly_percent=w.elderly_percent, outdoor_worker_density=w.outdoor_worker_density,
                demographic_multiplier=risk["demographic_multiplier"],
                breakdown=json.dumps({"base_risk": risk["base_risk"], "anomaly_score": risk.get("anomaly_score"),
                           "source": "celery-compute-risk"}),
            ))
            n += 1
        await session.commit()
    await engine.dispose()
    return {"status": "risk scores computed", "wards": n}


async def _trigger_async():
    engine = _engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as session:
        advisories = {a.risk_category: a for a in (await session.execute(select(AdvisoryTemplate))).scalars().all()}
        risks = (await session.execute(select(RiskScore).order_by(desc(RiskScore.created_at)).limit(200))).scalars().all()
        seen, created = set(), 0
        for r in risks:
            if r.ward_code in seen or r.risk_category not in ("HIGH", "SEVERE"):
                continue
            seen.add(r.ward_code)
            tmpl = advisories.get(r.risk_category)
            msg = (tmpl.sms_text if tmpl else f"{r.risk_category} heat risk in ward {r.ward_code}. Take precautions.")
            session.add(Alert(ward_code=r.ward_code, alert_channel="sms", message=msg,
                              triggered_by=r.risk_category, alert_status="sandbox",
                              external_id=f"celery_{r.ward_code}_{r.risk_category}"))
            created += 1
        await session.commit()
    await engine.dispose()
    return {"status": "alerts triggered", "created": created}


@celery_app.task(name="tasks.weather_tasks.refresh")
def refresh():
    return asyncio.run(_refresh_async())


@celery_app.task(name="tasks.risk_tasks.compute")
def compute():
    return asyncio.run(_compute_async())


@celery_app.task(name="tasks.alert_tasks.trigger")
def trigger():
    return asyncio.run(_trigger_async())
