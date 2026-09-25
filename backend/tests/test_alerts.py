"""Alert trigger: unknown wards rejected, bad categories rejected,
repeats deduped instead of stacking duplicates."""


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


def test_trigger_dedupes_same_ward_category(client):
    r1 = _trigger(client, ward_code="A", risk_category="HIGH", message="first")
    r2 = _trigger(client, ward_code="A", risk_category="HIGH", message="second")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]

    log = client.get("/api/alerts/").json()["alerts"]
    hits = [a for a in log if a["ward_code"] == "A" and a["triggered_by"] == "HIGH"]
    assert len(hits) == 1


def test_alert_log(client):
    r = client.get("/api/alerts/")
    assert r.status_code == 200
    assert isinstance(r.json()["alerts"], list)
