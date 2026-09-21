"""Seed wards from data/mumbai_ward_census.csv into PostgreSQL.

Reads the full Census CSV (97 Greater Mumbai wards) and upserts into the
``wards`` table. Safe to re-run: existing ward_codes are updated, missing
ones are inserted.

Usage:
    python scripts/seed_wards.py
"""
import asyncio
import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.db.session import Base
from app.models import Ward
from app.core.config import settings

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "mumbai_ward_census.csv")


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
        for row in rows:
            data = parse_row(row)
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
        await session.commit()

    await engine.dispose()
    print(f"Census rows: {len(rows)} | inserted: {inserted} | updated: {updated}")


if __name__ == "__main__":
    asyncio.run(seed_wards())
