"""Health endpoints must not be shadowed by dynamic /{ward_code} routes."""


def test_root_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_api_health_alias(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_wards_health_not_shadowed(client):
    """GET /api/wards/health used to 404 as 'Ward not found'."""
    r = client.get("/api/wards/health")
    assert r.status_code == 200
    assert r.json()["service"] == "heatwave-ews"
