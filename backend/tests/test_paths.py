"""Data/ML path resolution must survive both on-disk layouts.

Regression: the Dockerfile flattens ``backend/*`` into ``/app``, so the code
sits one level shallower than in the repo. A fixed ``../../..`` then resolved
to ``/`` instead of the app root, and because every failure was swallowed the
app served 200s with zero wards and an empty FeatureCollection — a blank map
with a healthy healthcheck.
"""
from pathlib import Path

import pytest

from app.core.paths import data_dir, forecast_path, geojson_path, resolve_dir


def _make_tree(root: Path, code_depth: int) -> Path:
    """Build a fake tree with the code nested ``code_depth`` dirs below root."""
    (root / "data").mkdir(parents=True)
    (root / "data" / "wards_geojson.json").write_text("{}")
    (root / "data" / "mumbai_ward_census.csv").write_text("ward_code\n")
    (root / "data" / "mumbai_weather_forecast.json").write_text("{}")
    code = root
    for name in ["app", "api", "services"][:code_depth]:
        code = code / name
    code.mkdir(parents=True)
    return code


@pytest.mark.parametrize("code_depth,label", [
    (3, "repo layout: Heatwave/backend/app/services"),
    (2, "container layout: /app/app/services"),
    (1, "shallow layout: /app/services"),
])
def test_resolves_data_dir_in_every_layout(tmp_path, code_depth, label, monkeypatch):
    code = _make_tree(tmp_path, code_depth)
    found = resolve_dir(code, "data", ("wards_geojson.json",))
    assert found == tmp_path / "data", f"wrong data dir in {label}"
    assert (found / "wards_geojson.json").exists()


def test_resolves_real_repo_data_dir():
    """The bundled data must be found from the real source tree."""
    d = data_dir()
    assert d.name == "data"
    assert (d / "wards_geojson.json").exists(), f"wards_geojson.json missing under {d}"
    assert (d / "mumbai_ward_census.csv").exists()
    assert geojson_path().parent == d
    assert forecast_path().parent == d


def test_env_override_wins(tmp_path, monkeypatch):
    custom = tmp_path / "elsewhere"
    custom.mkdir()
    monkeypatch.setenv("HEATWAVE_DATA_DIR", str(custom))
    assert data_dir() == custom


def test_fallback_is_reported_not_silently_empty(tmp_path):
    """With no data anywhere, return a concrete path rather than '/data'."""
    empty = tmp_path / "empty" / "app" / "services"
    empty.mkdir(parents=True)
    found = resolve_dir(empty, "data", ("wards_geojson.json",))
    assert found.is_absolute()
    assert found != Path("/data")
