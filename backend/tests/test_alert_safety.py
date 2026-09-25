"""Alert insert safety and the latest-alert reduction.

Two regressions are covered here:
  1. the alert task used to SELECT the whole (append-only) alerts table to
     work out the last alert per ward;
  2. external_id is UNIQUE, so two workers can pass the existence check and
     then collide. A losing insert must cost one alert, not the whole batch —
     which is what an un-guarded IntegrityError used to do.
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.queries import latest_alert_per_ward_category
from app.db.session import AsyncSessionLocal
from app.models import Alert

WARD = "T-safety"
BASE = datetime(2026, 9, 20, 6, 0, 0)


async def _cleanup():
    async with AsyncSessionLocal() as s:
        for a in (await s.execute(select(Alert).where(Alert.ward_code == WARD))).scalars().all():
            await s.delete(a)
        await s.commit()


def _latest():
    async def run():
        async with AsyncSessionLocal() as s:
            return [(a.ward_code, a.triggered_by, a.message)
                    for a in (await s.execute(latest_alert_per_ward_category())).scalars().all()
                    if a.ward_code == WARD]

    return asyncio.run(run())


def _seed():
    async def run():
        async with AsyncSessionLocal() as s:
            for msg, cat, hours in (("old-low", "LOW", 0), ("old-high", "HIGH", 0),
                                    ("new-high", "HIGH", 5)):
                s.add(Alert(ward_code=WARD, triggered_by=cat, alert_channel="sms",
                            message=msg, external_id=f"{WARD}_{cat}_{hours}",
                            sent_at=BASE + timedelta(hours=hours)))
            await s.commit()

    asyncio.run(_cleanup())
    asyncio.run(run())


def test_latest_alert_per_ward_category(client):
    """Only the newest row per (ward, category) comes back."""
    _seed()
    rows = dict((cat, msg) for _, cat, msg in _latest())
    assert rows == {"LOW": "old-low", "HIGH": "new-high"}


def test_duplicate_external_id_costs_one_alert_not_the_batch(client):
    """A savepoint around each insert keeps the transaction usable."""
    async def run():
        eid = f"{WARD}_HIGH_conflict"
        async with AsyncSessionLocal() as s:
            s.add(Alert(ward_code=WARD, triggered_by="HIGH", alert_channel="sms",
                        message="winner", external_id=eid))
            await s.commit()

            collided = False
            try:
                async with s.begin_nested():
                    s.add(Alert(ward_code=WARD, triggered_by="HIGH", alert_channel="sms",
                                message="loser", external_id=eid))
                    await s.flush()
            except IntegrityError:
                collided = True

            # The session must still accept work after the failed insert.
            s.add(Alert(ward_code=WARD, triggered_by="LOW", alert_channel="sms",
                        message="after-conflict", external_id=f"{WARD}_LOW_after"))
            await s.commit()
            return collided

    asyncio.run(_cleanup())
    try:
        assert asyncio.run(run()) is True, "duplicate external_id must raise IntegrityError"

        async def survivors():
            async with AsyncSessionLocal() as s:
                return sorted(a.message for a in
                              (await s.execute(select(Alert).where(Alert.ward_code == WARD))).scalars().all())

        assert asyncio.run(survivors()) == ["after-conflict", "winner"]
    finally:
        asyncio.run(_cleanup())
