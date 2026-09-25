"""Risk + config routers expose the canonical endpoints; nothing 500s."""
from datetime import datetime


def test_risk_map(client):
    r = client.get("/api/risk/wards")
    assert r.status_code == 200
    assert isinstance(r.json()["wards"], list)


def test_risk_for_unknown_ward_404(client):
    r = client.get("/api/risk/wards/ZZZZ")
    assert r.status_code == 404


def test_weather_unknown_ward_404(client):
    r = client.get("/api/weather/wards/ZZZZ/current")
    assert r.status_code == 404


def test_advisories_roundtrip(client):
    payload = {"HIGH": "Reschedule outdoor work."}
    r = client.post("/api/config/advisories", json=payload)
    assert r.status_code == 200
    rows = {row["risk_category"]: row for row in r.json()}
    assert rows["HIGH"]["sms_text"] == "Reschedule outdoor work."

    r = client.get("/api/config/advisories")
    assert r.status_code == 200


def test_openapi_lists_api_health():
    from app.main import app
    schema = app.openapi()
    assert "/api/health" in schema["paths"]
    assert "/api/wards/health" in schema["paths"]
    # removed duplicates must be gone from the API surface
    assert "/api/wards/config/thresholds" not in schema["paths"]
    assert "/api/wards/alerts/" not in schema["paths"]
    assert "/api/wards/risk/wards" not in schema["paths"]
