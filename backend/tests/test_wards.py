"""Ward routes: known ward, unknown ward, geojson, and removed duplicates."""


def test_list_wards(client):
    r = client.get("/api/wards/")
    assert r.status_code == 200
    codes = {w["ward_code"] for w in r.json()["wards"]}
    assert {"A", "B"} <= codes


def test_get_single_ward(client):
    r = client.get("/api/wards/A")
    assert r.status_code == 200
    assert r.json()["ward_name"] == "Ward A"


def test_unknown_ward_404(client):
    r = client.get("/api/wards/ZZZZ")
    assert r.status_code == 404


def test_geojson_shape(client):
    r = client.get("/api/wards/geojson")
    assert r.status_code == 200
    body = r.json()
    assert body["type"] == "FeatureCollection"
    assert isinstance(body["features"], list)


def test_duplicate_wards_routes_removed(client):
    """These lived only under /api/wards/* and duplicated the canonical
    /api/risk, /api/weather, /api/alerts, /api/config routers."""
    for path in (
        "/api/wards/risk/wards",
        "/api/wards/weather/wards/A/current",
        "/api/wards/config/thresholds",
        "/api/wards/alerts/",
    ):
        r = client.get(path)
        assert r.status_code == 404, f"{path} should be gone, got {r.status_code}"
