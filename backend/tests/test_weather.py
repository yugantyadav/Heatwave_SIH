"""Weather: current-hour selection (not the last forecast hour), forecast
file freshness, and the forecast endpoint."""
import json
import os
from datetime import datetime, timedelta

from app.services.weather import daily_heat_index_from_hourly, forecast_file_is_fresh
from app.tasks.weather_tasks import _pick_current_hour


def _hourly(days=5, start=None):
    start = start or datetime.now().replace(minute=0, second=0, microsecond=0)
    times, temps, rhs = [], [], []
    for d in range(days):
        for h in range(24):
            times.append((start + timedelta(days=d, hours=h)).isoformat(timespec="hours"))
            temps.append(30.0 + h / 4)
            rhs.append(70.0)
    return {"time": times, "temperature_2m": temps, "relative_humidity_2m": rhs}


def test_pick_current_hour_is_near_now_not_last():
    hourly = _hourly(days=5)
    idx = _pick_current_hour(hourly)
    chosen = datetime.fromisoformat(hourly["time"][idx])
    assert abs((chosen - datetime.now()).total_seconds()) <= 3600
    # The old code used index -1: day 5, 23:00 — days in the future.
    assert idx != len(hourly["time"]) - 1


def test_fresh_file_passes(tmp_path):
    path = tmp_path / "fc.json"
    path.write_text(json.dumps({"hourly": _hourly(5)}))
    assert forecast_file_is_fresh(str(path)) is True


def test_stale_file_fails(tmp_path):
    """Bundled file that ends before today must be treated as stale."""
    stale_start = datetime.now() - timedelta(days=10)
    path = tmp_path / "fc.json"
    path.write_text(json.dumps({"hourly": _hourly(5, start=stale_start)}))
    assert forecast_file_is_fresh(str(path)) is False


def test_partially_lapsed_file_fails(tmp_path):
    """Regression: checking only the LAST hourly slot reported a file written
    days ago as fresh, because its final slot was still in the future — the
    chart then rendered a truncated outlook instead of fetching live."""
    start = datetime.now().replace(minute=0, second=0, microsecond=0) - timedelta(days=3)
    path = tmp_path / "fc.json"
    path.write_text(json.dumps({"hourly": _hourly(5, start=start)}))
    data = json.loads(path.read_text())
    last = data["hourly"]["time"][-1]
    assert datetime.fromisoformat(last) > datetime.now(), "fixture must still end in the future"
    assert forecast_file_is_fresh(str(path)) is False


def test_file_starting_in_the_future_fails(tmp_path):
    start = datetime.now() + timedelta(days=2)
    path = tmp_path / "fc.json"
    path.write_text(json.dumps({"hourly": _hourly(5, start=start)}))
    assert forecast_file_is_fresh(str(path)) is False


def test_missing_file_fails(tmp_path):
    assert forecast_file_is_fresh(str(tmp_path / "nope.json")) is False


def test_daily_heat_index_forecast_shape():
    days = daily_heat_index_from_hourly(_hourly(5))
    assert 1 <= len(days) <= 5
    for d in days:
        assert set(d) >= {"date", "tmax", "heat_index", "wbgt"}
        assert d["heat_index"] > 0
    dates = [d["date"] for d in days]
    assert dates == sorted(dates)


def test_forecast_endpoint_returns_days(client):
    r = client.get("/api/weather/wards/A/forecast")
    assert r.status_code == 200
    body = r.json()
    assert body["ward_code"] == "A"
    assert isinstance(body["forecast"], list)
    today = datetime.now().date().isoformat()
    for day in body["forecast"]:
        # no stale (past) days may be served
        assert day["date"] >= today, f"stale forecast day: {day['date']}"


def test_current_weather_endpoint(client):
    r = client.get("/api/weather/wards/A/current")
    # 404 is acceptable pre-seed; the point is it must not 500
    assert r.status_code in (200, 404)
