"""latest_risk_per_ward() must reduce in the database.

The old implementation loaded every risk_scores row into Python on each map
request; the table is append-only, so that grew without bound. These tests
pin the SQL behaviour: exactly one (the newest) row per ward, and the
newest chosen by created_at with id as tie-breaker.
"""
import asyncio
from datetime import datetime, timedelta

from app.db.queries import latest_risk_per_ward
from app.db.session import AsyncSessionLocal
from app.models import RiskScore

BASE = datetime(2026, 9, 20, 6, 0, 0)


def _rows(client):
    """Seed a history where 'latest' is not simply the first or last inserted."""
    async def seed():
        async with AsyncSessionLocal() as s:
            for code in ("A", "B"):
                # three generations, oldest first
                for i, cat in enumerate(("LOW", "MODERATE", "HIGH")):
                    s.add(RiskScore(
                        ward_code=code, risk_category=cat, final_score=10.0 + i * 20,
                        created_at=BASE + timedelta(hours=i),
                    ))
            # a same-timestamp twin: id must break the tie
            s.add(RiskScore(ward_code="C", risk_category="LOW", final_score=5.0,
                            created_at=BASE))
            s.add(RiskScore(ward_code="C", risk_category="SEVERE", final_score=99.0,
                            created_at=BASE))
            await s.commit()

    async def fetch():
        async with AsyncSessionLocal() as s:
            result = await s.execute(latest_risk_per_ward())
            return [(r.ward_code, r.risk_category, r.final_score) for r in result.scalars().all()]

    asyncio.run(seed())
    return asyncio.run(fetch())


def test_returns_one_row_per_ward(client):
    rows = _rows(client)
    codes = [r[0] for r in rows]
    assert sorted(codes) == ["A", "B", "C"]
    assert len(codes) == len(set(codes)), "exactly one row per ward"


def test_returns_the_newest_row_per_ward(client):
    rows = {r[0]: r for r in _rows(client)}
    assert rows["A"][1] == "HIGH"
    assert rows["A"][2] == 50.0
    assert rows["B"][1] == "HIGH"
    # C's two rows share created_at, so the higher id (inserted later) wins
    assert rows["C"][1] == "SEVERE"
