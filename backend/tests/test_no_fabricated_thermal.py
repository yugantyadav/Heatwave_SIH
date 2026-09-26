"""A missing heat index must never be replaced by an invented number.

The compute pass used to substitute HI=35.0 / WBGT=28.0 when a reading had no
thermal values. A stale container running older code produced 105 NULL readings
and every ward was then scored from that constant while the pipeline still
reported success — a plausible-looking dashboard built on fabricated data.
"""
import asyncio

from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.models import RiskScore, Ward, WeatherReading
from app.services.alerting import utcnow
from app.tasks.weather_tasks import _compute_async

WARD = "T-null-hi"


async def _cleanup():
    async with AsyncSessionLocal() as s:
        await s.execute(delete(WeatherReading).where(WeatherReading.ward_code == WARD))
        await s.execute(delete(RiskScore).where(RiskScore.ward_code == WARD))
        await s.execute(delete(Ward).where(Ward.ward_code == WARD))
        await s.commit()


async def _seed_ward():
    """The compute pass walks Ward rows, so the ward itself must exist."""
    async with AsyncSessionLocal() as s:
        s.add(Ward(ward_code=WARD, ward_name="Thermal Gap Ward", zone="Z",
                   district="Mumbai", total_population=50_000,
                   elderly_percent=8.57, outdoor_worker_density=0.5))
        await s.commit()


async def _seed_reading(heat_index, wbgt):
    async with AsyncSessionLocal() as s:
        s.add(WeatherReading(ward_code=WARD, temperature_2m=30.0, relative_humidity_2m=70.0,
                             heat_index=heat_index, wbgt=wbgt, recorded_at=utcnow()))
        await s.commit()


def _scores_for_ward():
    async def run():
        async with AsyncSessionLocal() as s:
            return (await s.execute(select(RiskScore).where(RiskScore.ward_code == WARD))).scalars().all()

    return asyncio.run(run())


def test_wards_with_a_real_reading_are_scored(client):
    asyncio.run(_cleanup())
    try:
        asyncio.run(_seed_ward())
        asyncio.run(_seed_reading(42.0, 30.0))
        out = asyncio.run(_compute_async())
        rows = _scores_for_ward()
        assert len(rows) == 1, f"expected a score, got {len(rows)}"
        assert out.get("skipped_missing_thermal") is None
    finally:
        asyncio.run(_cleanup())


def test_ward_with_null_thermal_is_skipped_not_scored(client):
    asyncio.run(_cleanup())
    try:
        asyncio.run(_seed_ward())
        asyncio.run(_seed_reading(None, None))
        out = asyncio.run(_compute_async())
        assert _scores_for_ward() == [], "must not score a reading with no HI/WBGT"
        assert out.get("skipped_missing_thermal", 0) >= 1, "the shortfall must be reported"
    finally:
        asyncio.run(_cleanup())


def test_zero_thermal_is_treated_as_a_real_value(client):
    """0.0 is a measurement, not a gap — it must still be scored."""
    asyncio.run(_cleanup())
    try:
        asyncio.run(_seed_ward())
        asyncio.run(_seed_reading(0.0, 0.0))
        asyncio.run(_compute_async())
        rows = _scores_for_ward()
        assert len(rows) == 1, "0.0 is falsy but valid; it must not be skipped"
    finally:
        asyncio.run(_cleanup())


def test_pipeline_reports_thermal_shortfall(client, monkeypatch):
    """The failure must be visible in the pipeline result, not hidden."""
    from app.tasks import weather_tasks

    async def refresh_with_bad_thermal():
        engine = weather_tasks._engine()
        try:
            async with engine.begin() as conn:
                from app.db.session import Base
                await conn.run_sync(Base.metadata.create_all)
            async with AsyncSessionLocal() as s:
                s.add(WeatherReading(ward_code=WARD, temperature_2m=30.0,
                                     relative_humidity_2m=70.0,
                                     heat_index=None, wbgt=None, recorded_at=utcnow()))
                await s.commit()
            return {"status": "weather forecast refreshed", "wards": 1, "source": "test"}
        finally:
            await engine.dispose()

    monkeypatch.setattr(weather_tasks, "_refresh_async", refresh_with_bad_thermal)
    asyncio.run(_cleanup())
    asyncio.run(_seed_ward())
    try:
        out = asyncio.run(weather_tasks._pipeline_async())
        assert "compute" in out, out
        assert "skipped_missing_thermal" in out["compute"], out["compute"]
    finally:
        asyncio.run(_cleanup())
