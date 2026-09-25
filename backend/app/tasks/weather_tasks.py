"""Scheduled jobs: forecast refresh (6h) -> risk computation -> alert check.

Each task is idempotent and safe to run manually:
    celery -A app.tasks.celery_app worker --loglevel=info
    celery -A app.tasks.celery_app beat --loglevel=info

Uses synchronous SQLite (Celery worker process), no async engine needed.
"""
import asyncio
import json
import os

import aiohttp
from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.session import Base, AsyncSessionLocal
from app.db.queries import latest_alert_per_ward_category, latest_risk_per_ward
from app.models import AdvisoryTemplate, Alert, RiskScore, Ward, WeatherReading, ThresholdConfig
from app.services.alerting import ALERT_CATEGORIES, external_id_for, should_alert, utcnow
from app.services.risk_model import MortalityRiskService
from app.services.seeding import ensure_seeded
from app.services.thermal_index import ThermalIndexService
from app.tasks.celery_app import celery_app

MUMBAI_LAT, MUMBAI_LON = 19.076, 72.8777

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "heatwave.db"))


def _engine():
    return create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)


def _pick_current_hour(hourly: dict) -> int:
    """Index of the hourly slot closest to *now* (never a future day)."""
    from datetime import datetime

    times = hourly.get("time") or []
    if not times:
        return 0
    now = datetime.now()
    best, best_delta = 0, None
    for i, ts in enumerate(times[:96]):  # only scan the next/few days we ship
        try:
            dt = datetime.fromisoformat(str(ts))
        except ValueError:
            continue
        delta = abs((dt - now).total_seconds())
        if best_delta is None or delta < best_delta:
            best, best_delta = i, delta
    return best


async def _refresh_async():
    engine = _engine()
    params = {
        "latitude": MUMBAI_LAT,
        "longitude": MUMBAI_LON,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,weathercode",
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code",
        "timezone": "Asia/Kolkata",
        "forecast_days": 5,
    }
    fc_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "mumbai_weather_forecast.json"))
    # The data/ dir is absent in a fresh image unless the image copies it, so
    # never assume it is there.
    os.makedirs(os.path.dirname(fc_path), exist_ok=True)
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20) as resp:
                data = await resp.json()
        # Persist the fresh forecast so /api/weather/.../forecast never serves
        # a stale bundled file (atomic write: tmp + replace).
        tmp_path = fc_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, fc_path)
        cur = data.get("current") or {}
        if cur.get("temperature_2m") is not None:
            t = float(cur["temperature_2m"])
            rh = float(cur.get("relative_humidity_2m") or 0)
            pr = float(cur.get("precipitation") or 0)
            wc = int(cur.get("weather_code") or cur.get("weathercode") or 0)
        else:
            hourly = data.get("hourly", {})
            idx = _pick_current_hour(hourly)
            t = float(hourly["temperature_2m"][idx])
            rh = float(hourly["relative_humidity_2m"][idx])
            pr = float(hourly.get("precipitation", [0])[idx])
            wc = int(hourly.get("weathercode", [0])[idx])
        source = "open-meteo"
    except Exception:
        with open(fc_path) as f:
            fc = json.load(f)
        h = fc["hourly"]
        idx = _pick_current_hour(h)
        t = float(h["temperature_2m"][idx])
        rh = float(h["relative_humidity_2m"][idx])
        pr = float(h["precipitation"][idx])
        wc = int(h["weathercode"][idx])
        source = "bundled-fallback"
    th = ThermalIndexService.calculate(t, rh)
    try:
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
        return {"status": "weather forecast refreshed", "wards": n, "source": source,
                "temperature_2m": t, "heat_index": th.get("heat_index"), "wbgt": th.get("wbgt")}
    finally:
        await engine.dispose()


async def _compute_async():
    engine = _engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            wards = (await session.execute(select(Ward))).scalars().all()
            # Admin-panel thresholds override the model's default HI/WBGT cutoffs.
            cfg_rows = (await session.execute(select(ThresholdConfig))).scalars().all()
            thresholds = MortalityRiskService.thresholds_from_config(cfg_rows)
            n = 0
            for w in wards:
                wr = (await session.execute(
                    select(WeatherReading).where(WeatherReading.ward_code == w.ward_code)
                    .order_by(desc(WeatherReading.recorded_at)).limit(1))).scalar_one_or_none()
                if not wr:
                    continue
                # 0.0 is a real reading, not a missing one — only fall back on None.
                heat_index = wr.heat_index if wr.heat_index is not None else 35.0
                wbgt = wr.wbgt if wr.wbgt is not None else 28.0
                elderly = w.elderly_percent if w.elderly_percent is not None else 8.57
                workers = w.outdoor_worker_density if w.outdoor_worker_density is not None else 0.5
                risk = MortalityRiskService.calculate_risk(
                    heat_index=heat_index, wbgt=wbgt,
                    elderly_percent=elderly,
                    outdoor_worker_density=workers,
                    temperature_c=wr.temperature_2m, humidity=wr.relative_humidity_2m,
                    total_population=w.total_population,
                    thresholds=thresholds,
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
        return {"status": "risk scores computed", "wards": n}
    finally:
        await engine.dispose()


async def _trigger_async():
    engine = _engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        now = utcnow()
        cooldown = int(settings.ALERT_COOLDOWN_HOURS)
        async with AsyncSessionLocal() as session:
            advisories = {a.risk_category: a for a in (await session.execute(select(AdvisoryTemplate))).scalars().all()}
            risks = (await session.execute(latest_risk_per_ward())).scalars().all()
            # Only the newest alert per (ward, category) is needed — the log is
            # append-only, so reading it whole would grow every hourly run.
            last_alert_at = {
                (a.ward_code, a.triggered_by): a.sent_at
                for a in (await session.execute(latest_alert_per_ward_category())).scalars().all()
                if a.sent_at
            }
            created = 0
            for r in risks:
                if r.risk_category not in ALERT_CATEGORIES:
                    continue
                # A ward that re-escalates after the cooldown gets a fresh alert;
                # one stuck at HIGH re-alerts each time the cooldown lapses.
                if not should_alert(last_alert_at.get((r.ward_code, r.risk_category)), now, cooldown):
                    continue
                external_id = external_id_for("celery", r.ward_code, r.risk_category, now, cooldown * 3600)
                if (await session.execute(
                    select(Alert).where(Alert.external_id == external_id)
                )).scalars().first():
                    continue
                tmpl = advisories.get(r.risk_category)
                msg = (tmpl.sms_text if tmpl else f"{r.risk_category} heat risk in ward {r.ward_code}. Take precautions.")
                # external_id is UNIQUE, so a concurrent worker can still win the
                # race between the check above and this insert. Each insert gets
                # its own SAVEPOINT so losing that race costs one alert instead
                # of aborting every alert queued in this run.
                try:
                    async with session.begin_nested():
                        session.add(Alert(ward_code=r.ward_code, alert_channel="sms", message=msg,
                                          triggered_by=r.risk_category, alert_status="sandbox",
                                          external_id=external_id))
                        await session.flush()
                except IntegrityError:
                    continue
                created += 1
            await session.commit()
        return {"status": "alerts triggered", "created": created}
    finally:
        await engine.dispose()


async def _pipeline_async():
    """seed -> refresh -> compute -> trigger, in order.

    Seeding comes first because a fresh deployment (or an expired free
    Postgres) has the tables but no rows: without wards the map renders
    nothing, and the risk pass would score zero wards.

    refresh/compute/trigger used to be three independent beat entries
    sharing one period, so they fired at the same instant and compute could
    read the previous refresh's weather. Running them in sequence guarantees
    risk is scored from fresh weather and alerts follow the scores they were
    meant to act on.
    """
    results = {}
    for name, step in (
        ("seed", _seed_async),
        ("refresh", _refresh_async),
        ("compute", _compute_async),
        ("trigger", _trigger_async),
    ):
        try:
            results[name] = await step()
        except Exception as exc:  # one broken step must not starve the others
            results[name] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return results


async def _seed_async():
    engine = _engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            return await ensure_seeded(session)
    finally:
        await engine.dispose()


@celery_app.task(name="tasks.weather_tasks.pipeline")
def pipeline():
    return asyncio.run(_pipeline_async())


@celery_app.task(name="tasks.weather_tasks.refresh")
def refresh():
    return asyncio.run(_refresh_async())


@celery_app.task(name="tasks.risk_tasks.compute")
def compute():
    return asyncio.run(_compute_async())


@celery_app.task(name="tasks.alert_tasks.trigger")
def trigger():
    return asyncio.run(_trigger_async())
