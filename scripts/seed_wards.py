"""Seed wards into PostgreSQL.

1. Upserts the full Census CSV (97 Greater Mumbai census wards) — the
   demographic backbone (populations, SC/ST counts).
2. Upserts the 8 area-specific map wards from data/wards_geojson.json
   (Colaba, Dadar, Bandra West, Andheri West, Malad, Borivali, Kurla,
   Chembur at their real centers) — the dashboard's map layer.

Safe to re-run: existing ward_codes are updated, missing ones inserted.

Usage:
    python scripts/seed_wards.py
"""
import asyncio
import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.session import Base
from app.models import Ward
from app.core.config import settings

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mumbai_ward_census.csv")
AREAS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "wards_geojson.json")


def parse_row(row):
    code = row["Ward Code"].strip()
    wname = row["Ward Name"].strip()
    return {
        "ward_code": code,
        "ward_name": f"Ward {code} ({wname})",
        "zone": wname,
        "district": row["District Name"].strip(),
        "total_population": int(row["Total Population"] or 0),
        "total_males": int(row["Total Males"] or 0),
        "total_females": int(row["Total Females"] or 0),
        "sc_population": int(row["SC Population"] or 0),
        "st_population": int(row["ST Population"] or 0),
        # Prototype defaults (documented, not census-measured):
        "elderly_percent": 8.57,
        "outdoor_worker_density": 0.5,
    }


async def seed_wards():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))

    async with AsyncSession(engine) as session:
        inserted, updated = 0, 0

        async def upsert(data):
            nonlocal inserted, updated
            result = await session.execute(
                select(Ward).where(Ward.ward_code == data["ward_code"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                session.add(Ward(**data))
                inserted += 1

        for row in rows:
            await upsert(parse_row(row))
        census_n = len(rows)

        # Area-specific map wards (same codes the dashboard queries).
        with open(AREAS_PATH) as f:
            areas = json.load(f)["features"]
        for feat in areas:
            p = feat["properties"]
            await upsert({
                "ward_code": str(p["ward_code"]),
                "ward_name": p["ward_name"],
                "zone": p.get("zone"),
                "district": p.get("district"),
                "total_population": int(p.get("total_population") or 0),
                "total_males": 0,
                "total_females": 0,
                "sc_population": 0,
                "st_population": 0,
                "elderly_percent": float(p.get("elderly_percent") or 8.57),
                "outdoor_worker_density": 0.5,
            })
        await session.commit()

    await engine.dispose()
    print(f"Census rows: {census_n} | areas: {len(areas)} | inserted: {inserted} | updated: {updated}")


if __name__ == "__main__":
    asyncio.run(seed_wards())
