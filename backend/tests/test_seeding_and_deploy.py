"""Boot-time seeding and deploy-time config normalisation.

These cover the two things that silently produced a *healthy but empty* app
on a fresh deploy: tables created with no rows, and a sync-driver database
URL that an async engine cannot use.
"""
import asyncio

import pytest
from sqlalchemy import delete, func, select

from app.core.config import Settings
from app.db.session import AsyncSessionLocal
from app.models import AdvisoryTemplate, ThresholdConfig, Ward
from app.services.seeding import DEFAULT_ADVISORIES, DEFAULT_THRESHOLDS, ensure_seeded, load_ward_rows


async def _wipe():
    async with AsyncSessionLocal() as s:
        await s.execute(delete(Ward))
        await s.execute(delete(ThresholdConfig))
        await s.execute(delete(AdvisoryTemplate))
        await s.commit()


async def _ensure_fixture_wards():
    """Restore the A/B wards exactly as conftest created them.

    These tests empty the wards table and re-seed it from data/, where ward
    code "A" is the real Colaba polygon. Other modules assert on the conftest
    fixture, so overwrite rather than skip to put that state back.
    """
    async with AsyncSessionLocal() as s:
        for code, name, zone, pop in (("A", "Ward A", "Zone 1", 120000),
                                      ("B", "Ward B", "Zone 2", 80000)):
            row = (await s.execute(select(Ward).where(Ward.ward_code == code))).scalar_one_or_none()
            if row is None:
                row = Ward(ward_code=code)
                s.add(row)
            row.ward_name = name
            row.zone = zone
            row.district = "Mumbai"
            row.total_population = pop
            row.elderly_percent = 8.57
            row.outdoor_worker_density = 0.5
            row.geometry = None
        await s.commit()


@pytest.fixture(autouse=True)
def _preserve_shared_fixtures(client):
    """Depend on `client` so the tables exist no matter the run order, then
    put conftest's A/B wards back after each test."""
    yield
    asyncio.run(_ensure_fixture_wards())


def test_data_files_are_present_in_the_repo():
    """The container copies data/; without it seeding is a silent no-op."""
    rows = load_ward_rows()
    assert rows, "no ward rows parsed from data/"
    assert any(r.get("geometry") for r in rows), "no polygon-backed map wards parsed"
    assert any(not r.get("geometry") for r in rows), "no census-only wards parsed"


def test_ensure_seeded_fills_an_empty_database(client):
    """Wipe, seed and verify inside ONE session so no other test can interleave."""
    async def run():
        async with AsyncSessionLocal() as s:
            await s.execute(delete(Ward))
            await s.execute(delete(ThresholdConfig))
            await s.execute(delete(AdvisoryTemplate))
            await s.commit()

            async def counts():
                return {
                    "wards": (await s.execute(select(func.count()).select_from(Ward))).scalar_one(),
                    "thresholds": (await s.execute(select(func.count()).select_from(ThresholdConfig))).scalar_one(),
                    "advisories": (await s.execute(select(func.count()).select_from(AdvisoryTemplate))).scalar_one(),
                }

            assert await counts() == {"wards": 0, "thresholds": 0, "advisories": 0}, \
                "premise: database must be empty before seeding"

            out = await ensure_seeded(s)

            assert out["wards"] > 0
            assert out["thresholds"] == len(DEFAULT_THRESHOLDS)
            assert out["advisories"] == len(DEFAULT_ADVISORIES)

            after = await counts()
            assert after["wards"] > 0
            assert after["thresholds"] == 2
            assert after["advisories"] == 4
            return out

    asyncio.run(run())


def test_ensure_seeded_does_not_clobber_existing_rows(client):
    """Admin edits must survive a restart, so seeding only fills gaps."""
    async def seed_then_edit():
        async with AsyncSessionLocal() as s:
            await ensure_seeded(s)
            row = (await s.execute(
                select(ThresholdConfig).where(ThresholdConfig.config_type == "heat_index")
            )).scalar_one()
            row.low_threshold = 41.5
            await s.commit()

    asyncio.run(seed_then_edit())

    async def reseed_and_read():
        async with AsyncSessionLocal() as s:
            out = await ensure_seeded(s)
            row = (await s.execute(
                select(ThresholdConfig).where(ThresholdConfig.config_type == "heat_index")
            )).scalar_one()
            return out, row.low_threshold

    out, value = asyncio.run(reseed_and_read())
    assert out["wards"] == 0, "wards already present, nothing to insert"
    assert out["thresholds"] == 0, "thresholds already present"
    assert out["skipped"] is True
    assert value == 41.5, "an admin's threshold edit was overwritten"


def test_severe_threshold_is_seeded_blank_not_zero():
    """0 is not a valid temperature cutoff and the Admin editor rejects it."""
    for row in DEFAULT_THRESHOLDS:
        assert row["severe_threshold"] is None
        for key, value in row.items():
            if key.endswith("_threshold") and value is not None:
                assert value > 0


@pytest.mark.parametrize("raw,expected", [
    # Render hands out a sync-driver URL; the async engine needs asyncpg.
    ("postgresql://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
    ("postgres://u:p@h:5432/db", "postgresql+asyncpg://u:p@h:5432/db"),
    ("postgresql+psycopg2://u:p@h/db", "postgresql+asyncpg://u:p@h/db"),
    # already async, or not postgres: left alone
    ("sqlite+aiosqlite:////tmp/x.db", "sqlite+aiosqlite:////tmp/x.db"),
])
def test_async_database_url_normalisation(raw, expected):
    assert Settings(DATABASE_URL=raw).ASYNC_DATABASE_URL == expected


def test_render_yaml_has_no_paid_services():
    """Free tier only: no background worker and no Key Value instance."""
    import pathlib

    yaml = pytest.importorskip("yaml")
    path = pathlib.Path(__file__).resolve().parents[2] / "render.yaml"
    blueprint = yaml.safe_load(path.read_text())
    # Render omits "type" for Postgres and uses it to select other datastores,
    # so a redis instance here would show up as type == "redis".
    assert all(db.get("type") != "redis" for db in blueprint["databases"])
    assert all(s["type"] == "web" for s in blueprint["services"]), "only a web service is free"
    assert blueprint["databases"][0]["plan"] == "free"
    assert "healthCheckPath" in blueprint["services"][0]
