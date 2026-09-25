"""Ingest weather + compute risk scores for every ward.

Sources (in priority order):
  1. data/mumbai_weather_forecast.json (Open-Meteo hourly, real)
  2. data/mumbai_weather_real.csv      (17k hourly rows, real fallback)

For each ward in the DB this script:
  - takes the latest forecast hour as "current" conditions,
  - computes Heat Index / WBGT via ml/thermal_engine.py when available
    (Lu & Romps 2022 HI + WBGT), falling back to a Rothfusz approximation,
  - scores mortality-weighted risk via backend MortalityRiskService,
  - upserts one WeatherReading + one RiskScore per ward,
  - stores the 5-day daily maxima as the forecast payload source.

Usage:
    python scripts/ingest_weather.py [--wards all]
"""
import argparse
import asyncio
import csv
import json
import math
import os
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "ml"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.session import Base
from app.models import Ward, WeatherReading, RiskScore, ThresholdConfig
from app.core.config import settings
from app.services.risk_model import MortalityRiskService

FORECAST_JSON = os.path.join(ROOT, "data", "mumbai_weather_forecast.json")
REAL_CSV = os.path.join(ROOT, "data", "mumbai_weather_real.csv")

try:
    from thermal_engine import calculate_thermal_indices as ml_thermal

    HAVE_ML = True
except Exception:
    HAVE_ML = False


def rothfusz_hi_fallback(t_c: float, rh: float) -> float:
    """Rothfusz regression in °F converted back to °C (fallback only)."""
    t_f = t_c * 9 / 5 + 32
    hi_f = (
        -42.379
        + 2.04901523 * t_f
        + 10.14333127 * rh
        - 0.22475541 * t_f * rh
        - 0.00683783 * t_f * t_f
        - 0.05481717 * rh * rh
        + 0.00122874 * t_f * t_f * rh
        + 0.00085282 * t_f * rh * rh
        - 0.00000199 * t_f * t_f * rh * rh
    )
    return round((hi_f - 32) * 5 / 9, 1)


def thermal(t_c: float, rh: float):
    if HAVE_ML:
        try:
            out = ml_thermal(temperature=t_c, humidity=rh)
            hi = float(out.get("heat_index", 0))
            wb = float(out.get("wbgt", 0))
            if math.isnan(hi) or math.isnan(wb):
                raise ValueError("NaN from ML engine")
            return round(hi, 1), round(wb, 1)
        except Exception:
            pass
    hi = rothfusz_hi_fallback(t_c, rh)
    wb = round(0.7 * (t_c * math.atan(0.151977 * math.sqrt(rh + 8.313659))
                      + math.atan(t_c + rh) - math.atan(rh - 1.676331)
                      + 0.00391838 * rh ** 1.5 * math.atan(0.023101 * rh)
                      - 4.686035), 1)
    return hi, wb


def load_current_and_daily():
    from datetime import datetime

    with open(FORECAST_JSON) as f:
        fc = json.load(f)
    hourly = fc["hourly"]
    # Hour closest to *now* — not the last forecast hour (which is days ahead).
    now = datetime.now()
    idx, best = 0, None
    for i, ts in enumerate(hourly["time"][:96]):
        try:
            dt = datetime.fromisoformat(str(ts))
        except ValueError:
            continue
        d = abs((dt - now).total_seconds())
        if best is None or d < best:
            idx, best = i, d
    cur = {
        "temperature_2m": float(hourly["temperature_2m"][idx]),
        "relative_humidity_2m": float(hourly["relative_humidity_2m"][idx]),
        "precipitation": float(hourly["precipitation"][idx]),
        "weathercode": int(hourly["weathercode"][idx]),
    }
    daily = fc.get("daily", {})
    days = []
    for i, d in enumerate(daily.get("time", [])):
        tmax = daily["temperature_2m_max"][i]
        hi, wb = thermal(float(tmax), cur["relative_humidity_2m"])
        days.append({"date": d, "tmax": tmax, "heat_index": hi, "wbgt": wb})
    return cur, days


async def ingest(limit: int | None = None):
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cur, days = load_current_and_daily()
    hi, wb = thermal(cur["temperature_2m"], cur["relative_humidity_2m"])

    async with AsyncSession(engine) as session:
        result = await session.execute(select(Ward).order_by(Ward.ward_code))
        wards = result.scalars().all()
        if limit:
            wards = wards[:limit]
        cfg_rows = (await session.execute(select(ThresholdConfig))).scalars().all()
        thresholds = MortalityRiskService.thresholds_from_config(cfg_rows)
        for w in wards:
            reading = WeatherReading(
                ward_code=w.ward_code,
                temperature_2m=cur["temperature_2m"],
                relative_humidity_2m=cur["relative_humidity_2m"],
                precipitation=cur["precipitation"],
                weathercode=cur["weathercode"],
                heat_index=hi,
                wbgt=wb,
            )
            session.add(reading)
            # 0.0 is a real value, not a missing one — only fall back on None.
            elderly = w.elderly_percent if w.elderly_percent is not None else 8.57
            workers = w.outdoor_worker_density if w.outdoor_worker_density is not None else 0.5
            risk = MortalityRiskService.calculate_risk(
                heat_index=hi,
                wbgt=wb,
                elderly_percent=elderly,
                outdoor_worker_density=workers,
                total_population=w.total_population,
                thresholds=thresholds,
            )
            existing_risk = await session.execute(
                select(RiskScore).where(RiskScore.ward_code == w.ward_code)
                .order_by(RiskScore.id.desc()).limit(1)
            )
            existing = existing_risk.scalar_one_or_none()
            if existing:
                existing.risk_category = str(risk["risk_category"]).upper()
                existing.final_score = risk["final_score"]
                existing.heat_index = hi
                existing.wbgt = wb
                existing.elderly_percent = w.elderly_percent
                existing.outdoor_worker_density = w.outdoor_worker_density
                existing.demographic_multiplier = risk["demographic_multiplier"]
                existing.breakdown = json.dumps({"base_risk": risk["base_risk"], "source": "ingest_weather.py"})
            else:
                session.add(
                    RiskScore(
                        ward_code=w.ward_code,
                        risk_category=str(risk["risk_category"]).upper(),
                        final_score=risk["final_score"],
                        heat_index=hi,
                        wbgt=wb,
                        elderly_percent=w.elderly_percent,
                        outdoor_worker_density=w.outdoor_worker_density,
                        demographic_multiplier=risk["demographic_multiplier"],
                    breakdown=json.dumps({"base_risk": risk["base_risk"], "source": "ingest_weather.py"}),
                )
                )
        await session.commit()
        count = len(wards)
    await engine.dispose()
    print(f"Ingested current wx (T={cur['temperature_2m']}C RH={cur['relative_humidity_2m']}%) "
          f"HI={hi} WBGT={wb} ML={HAVE_ML} for {count} wards; forecast days={len(days)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--wards", default="all")
    args = ap.parse_args()
    limit = None if args.wards == "all" else int(args.wards)
    asyncio.run(ingest(limit))
