"""Threshold config: Severe can be blanked (null, not 0) and saved again."""


def test_get_thresholds(client):
    r = client.get("/api/config/thresholds")
    assert r.status_code == 200
    rows = r.json()
    types = {row["config_type"] for row in rows}
    assert {"heat_index", "wbgt"} <= types


def test_severe_blank_roundtrip(client):
    """Blank Severe used to be stored as 0 on insert and could never be
    cleared again (update skipped nulls), deadlocking the editor."""
    payload = {
        "Low": {"maxHeatIndexC": 30, "maxWbgtC": 27},
        "Moderate": {"maxHeatIndexC": 39, "maxWbgtC": 30},
        "High": {"maxHeatIndexC": 48, "maxWbgtC": 39},
        "Severe": {"maxHeatIndexC": None, "maxWbgtC": None},
    }
    r = client.post("/api/config/thresholds", json=payload)
    assert r.status_code == 200
    rows = {row["config_type"]: row for row in r.json()}
    # null must survive the roundtrip — never coerced to 0
    assert rows["heat_index"]["severe_threshold"] is None
    assert rows["wbgt"]["severe_threshold"] is None
    assert rows["heat_index"]["low_threshold"] == 30

    # re-saving with a value fills it back in
    payload["Severe"] = {"maxHeatIndexC": 55, "maxWbgtC": 45}
    r = client.post("/api/config/thresholds", json=payload)
    assert r.status_code == 200
    rows = {row["config_type"]: row for row in r.json()}
    assert rows["heat_index"]["severe_threshold"] == 55
    assert rows["wbgt"]["severe_threshold"] == 45
