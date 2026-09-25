"""Seed wards into the database.

This is the manual/CLI path. The same logic runs automatically at the start
of every pipeline (see app/services/seeding.py), so a fresh deployment
self-seeds; this script exists for re-seeding or backfilling a local DB.

1. Upserts the full Census CSV (Greater Mumbai census wards) — the
   demographic backbone (populations, SC/ST counts).
2. Upserts the 8 area-specific map wards from data/wards_geojson.json
   (Colaba, Dadar, Bandra West, Andheri West, Malad, Borivali, Kurla,
   Chembur at their real centers) — the dashboard's map layer.

Safe to re-run: existing ward_codes are updated, missing ones inserted.

Usage:
    python scripts/seed_wards.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.db.session import Base
from app.models import Ward
from app.services.seeding import ensure_seeded


async def seed_wards():
    engine = create_async_engine(settings.ASYNC_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ensure_seeded only fills an empty table; the CLI is a full upsert.
    async def upsert_all():
        from app.db.session import AsyncSessionLocal
        from app.services.seeding import load_ward_rows

        inserted = updated = 0
        async with AsyncSessionLocal() as session:
            for data in load_ward_rows():
                existing = (await session.execute(
                    select(Ward).where(Ward.ward_code == data["ward_code"])
                )).scalar_one_or_none()
                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                    updated += 1
                else:
                    session.add(Ward(**data))
                    inserted += 1
            await session.commit()
        return inserted, updated

    inserted, updated = await upsert_all()
    result = await _seed_thresholds_and_advisories()
    await engine.dispose()
    print(f"Wards: inserted={inserted} updated={updated} | "
          f"thresholds+advisories={result}")


async def _seed_thresholds_and_advisories():
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        return await ensure_seeded(session)


if __name__ == "__main__":
    asyncio.run(seed_wards())
