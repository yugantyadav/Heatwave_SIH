"""Thermal indices must be real numbers, never None.

Regression cover for three silent failures that only appeared inside the
container: the ml/ path resolved to / (so the preferred engine never loaded),
pythermalcomfort 3.8 moved heat_index_lu/wbgt out of `utilities` (so the
"fallback" raised), and every exception was swallowed into a None that let the
risk pass substitute a fabricated HI of 35 degrees.
"""
import pytest

from app.services import thermal_index
from app.services.thermal_index import ThermalIndexService
from app.services.risk_model import MortalityRiskService

# (temp C, RH %) across the range a Mumbai day actually hits
CASES = [(24, 85), (27, 80), (29.3, 70), (33, 55), (38, 40), (40, 30)]


@pytest.mark.parametrize("temp,rh", CASES)
def test_heat_index_and_wbgt_are_numbers(temp, rh):
    out = ThermalIndexService.calculate(temp, rh)
    assert out["heat_index"] is not None, "HI must never be None"
    assert out["wbgt"] is not None, "WBGT must never be None"
    assert isinstance(out["heat_index"], (int, float))
    assert isinstance(out["wbgt"], (int, float))


def test_heat_index_is_plausible_for_mumbai():
    """HI tracks temperature and stays in a physically sensible band."""
    cool = ThermalIndexService.calculate(24, 85)
    mild = ThermalIndexService.calculate(29, 70)
    hot = ThermalIndexService.calculate(38, 40)
    assert cool["heat_index"] < mild["heat_index"] < hot["heat_index"]
    for temp, rh in CASES:
        hi = ThermalIndexService.calculate(temp, rh)["heat_index"]
        assert 0 <= hi <= 70, f"implausible HI {hi} at {temp}C/{rh}%"


def test_wbgt_below_dry_bulb_in_moderate_conditions():
    """WBGT sits below air temperature outside peak solar load."""
    for temp, rh in CASES:
        wb = ThermalIndexService.calculate(temp, rh)["wbgt"]
        assert wb <= temp + 0.2, f"WBGT {wb} exceeds T {temp}"


def test_humidity_raises_heat_index():
    dry = ThermalIndexService.calculate(32, 30)["heat_index"]
    humid = ThermalIndexService.calculate(32, 80)["heat_index"]
    assert humid > dry


def test_internal_rothfusz_is_always_available():
    """Last resort must not depend on either library."""
    hi = thermal_index._rothfusz_hi(29.3, 70)
    wb = thermal_index._rothfusz_wbgt(29.3, 70)
    assert isinstance(hi, float) and 0 < hi < 70
    assert isinstance(wb, float) and wb < 29.3


def test_ml_engine_is_discovered():
    """The preferred engine must be found from the real source tree.

    This is the check that fails in the container if ml/ is mis-resolved."""
    assert thermal_index._HAVE_ML, "ml/thermal_engine.py not importable"
    out = ThermalIndexService.calculate(29.3, 70)
    assert out["source"] == "ml/thermal_engine.py"


def test_anomaly_model_is_discovered():
    """Same for the Isolation Forest: if this is False the blend is silently off."""
    assert MortalityRiskService.USE_ML_ANOMALY, "ml/risk_model.py not importable"
    assert MortalityRiskService.MODEL_PATH, "anomaly model path not resolved"
    import os
    assert os.path.exists(MortalityRiskService.MODEL_PATH), MortalityRiskService.MODEL_PATH


def test_calculate_batch_matches_single():
    rows = [{"temperature_c": t, "relative_humidity": r} for t, r in CASES[:3]]
    batch = ThermalIndexService.calculate_batch(rows)
    assert len(batch) == 3
    for (t, r), out in zip(CASES[:3], batch):
        assert out["heat_index"] == ThermalIndexService.calculate(t, r)["heat_index"]
