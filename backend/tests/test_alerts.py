"""Alert trigger: unknown wards rejected, bad categories rejected,
double-sends collapsed, but genuine later re-alerts are allowed."""
import asyncio
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal
from app.models import Alert
from app.services.alerting import external_id_for, should_alert, utcnow


def _trigger(client, **kw):
    payload = {
        "ward_code": "A",
        "risk_category": "HIGH",
        "message": "Heat alert",
        "channel": "sms",
    }
    payload.update(kw)
    return client.post("/api/alerts/trigger", json=payload)


def test_trigger_known_ward(client):
    r = _trigger(client, ward_code="B", risk_category="SEVERE", message="Severe heat")
    assert r.status_code == 200
    body = r.json()
    assert body["ward_code"] == "B"
    assert body["triggered_by"] == "SEVERE"


def test_trigger_unknown_ward_404(client):
    r = _trigger(client, ward_code="ZZZZ")
    assert r.status_code == 404


def test_trigger_unknown_category_400(client):
    r = _trigger(client, risk_category="BOGUS")
    assert r.status_code == 400


def test_double_send_inside_window_is_collapsed(client):
    """A double-click must not stack two rows."""
    r1 = _trigger(client, ward_code="A", risk_category="HIGH", message="first")
    r2 = _trigger(client, ward_code="A", risk_category="HIGH", message="second")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]

    log = client.get("/api/alerts/").json()["alerts"]
    hits = [a for a in log if a["ward_code"] == "A" and a["triggered_by"] == "HIGH"]
    assert len(hits) == 1


def test_realert_is_allowed_once_the_window_lapses(client):
    """The old scheme keyed on (ward, category) forever, so a ward could only
    ever alert once — a re-escalation days later was silently dropped."""
    first = _trigger(client, ward_code="B", risk_category="MODERATE", message="first")
    assert first.status_code == 200

    async def age_the_alert(alert_id):
        # Pretend the earlier alert belongs to a window that has passed.
        stale = external_id_for("demo", "B", "MODERATE", utcnow() - timedelta(hours=2), 300)
        async with AsyncSessionLocal() as s:
            row = await s.get(Alert, alert_id)
            row.external_id = stale
            await s.commit()

    asyncio.run(age_the_alert(first.json()["id"]))

    second = _trigger(client, ward_code="B", risk_category="MODERATE", message="second")
    assert second.status_code == 200
    assert second.json()["id"] != first.json()["id"]


def test_external_id_buckets_by_window():
    t0 = datetime(2026, 9, 25, 10, 0, 0)
    a = external_id_for("celery", "A", "HIGH", t0, 3600)
    b = external_id_for("celery", "A", "HIGH", t0 + timedelta(minutes=30), 3600)
    c = external_id_for("celery", "A", "HIGH", t0 + timedelta(hours=7), 3600)
    assert a == b, "same window must collapse to one id"
    assert a != c, "a later window must get its own id"
    assert a.startswith("celery_A_HIGH_")


def test_should_alert_respects_cooldown():
    now = utcnow()
    assert should_alert(None, now, 6) is True
    assert should_alert(now - timedelta(minutes=5), now, 6) is False
    assert should_alert(now - timedelta(hours=7), now, 6) is True


def test_alert_log(client):
    r = client.get("/api/alerts/")
    assert r.status_code == 200
    assert isinstance(r.json()["alerts"], list)


def test_alert_timestamps_carry_utc_offset(client):
    """Offset-less UTC strings are parsed by browsers as local time."""
    alerts = client.get("/api/alerts/").json()["alerts"]
    assert alerts
    for alert in alerts:
        assert alert["sent_at"].endswith("+00:00") or alert["sent_at"].endswith("Z")
