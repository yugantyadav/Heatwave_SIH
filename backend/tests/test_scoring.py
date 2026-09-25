"""Scoring path: admin thresholds feed the model, population spreads scores,
a zero ML anomaly never haircuts the thermal score."""
from types import SimpleNamespace

from app.services.risk_model import MortalityRiskService as M


def _cfg(hi=(29, 38, 47), wb=(27, 30, 39)):
    return [
        SimpleNamespace(config_type="heat_index", low_threshold=hi[0],
                        moderate_threshold=hi[1], high_threshold=hi[2],
                        severe_threshold=None),
        SimpleNamespace(config_type="wbgt", low_threshold=wb[0],
                        moderate_threshold=wb[1], high_threshold=wb[2],
                        severe_threshold=58),
    ]


def test_thresholds_from_config_maps_admin_maxes():
    th = M.thresholds_from_config(_cfg())
    # Low's max HI is where Moderate begins, etc.
    assert th["hi_threshold_moderate"] == 29
    assert th["hi_threshold_high"] == 38
    assert th["hi_threshold_severe"] == 47
    assert th["wbgt_threshold_moderate"] == 27
    assert th["wbgt_threshold_high"] == 30
    assert th["wbgt_threshold_severe"] == 39


def test_thresholds_from_config_skips_zero_and_missing():
    rows = [SimpleNamespace(config_type="heat_index", low_threshold=0,
                            moderate_threshold=38, high_threshold=None,
                            severe_threshold=None)]
    th = M.thresholds_from_config(rows)
    assert th == {"hi_threshold_high": 38}


def test_admin_thresholds_change_base_risk():
    th = M.thresholds_from_config(_cfg())
    # HI 42: default severe cutoff is 41 (base ~66.5); admin cutoff is 47
    # so the same heat should score lower under admin thresholds.
    default_base = M._base_risk_from_thermal(42, 30)
    admin_base = M._base_risk_from_thermal(42, 30, th)
    assert admin_base < default_base


def test_default_path_unchanged_without_thresholds():
    assert M._base_risk_from_thermal(42, 30) == M._base_risk_from_thermal(42, 30, None)


def test_population_weight_spreads_scores():
    kwargs = dict(heat_index=35, wbgt=28, elderly_percent=8.57,
                  outdoor_worker_density=0.5)
    small = M.calculate_risk(**kwargs, total_population=10_000)
    big = M.calculate_risk(**kwargs, total_population=2_000_000)
    assert big["final_score"] > small["final_score"]


def test_zero_anomaly_does_not_haircut(monkeypatch):
    """An anomaly score of 0 means 'normal' and must never reduce risk."""
    monkeypatch.setattr(M, "USE_ML_ANOMALY", True)
    kwargs = dict(heat_index=42, wbgt=30, elderly_percent=8.57,
                  outdoor_worker_density=0.5, temperature_c=42, humidity=60)
    monkeypatch.setattr("app.services.risk_model._ml_anomaly",
                        lambda *a, **k: ("normal", 0.0))
    out = M.calculate_risk(**kwargs)
    no_ml = M.calculate_risk(heat_index=42, wbgt=30, elderly_percent=8.57,
                             outdoor_worker_density=0.5)
    assert out["final_score"] == no_ml["final_score"]


def test_category_cutoffs():
    assert M._category(10) == "LOW"
    assert M._category(30) == "MODERATE"
    assert M._category(50) == "HIGH"
    assert M._category(75) == "SEVERE"
    assert M._category(100) == "SEVERE"
