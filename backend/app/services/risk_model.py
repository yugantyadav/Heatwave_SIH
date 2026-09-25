# Risk model service
# Prototype mortality-weighted scorer. Optionally blends the Isolation Forest
# anomaly score from ml/models/isolation_forest.joblib (loaded by
# ml/risk_model.py) when the ml package is importable.
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml"))

try:
    from risk_model import detect_heat_anomaly as _ml_anomaly

    _HAVE_ML_ANOMALY = True
    _MODEL_PATH = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "ml", "models", "isolation_forest.joblib"
    )
except Exception:
    _HAVE_ML_ANOMALY = False
    _MODEL_PATH = None


class MortalityRiskService:
    MODEL_PATH = os.path.normpath(_MODEL_PATH) if _MODEL_PATH else None
    USE_ML_ANOMALY = _HAVE_ML_ANOMALY
    DEFAULT_COEFFICIENTS = {
        "elderly_weight": 0.15,
        "outdoor_worker_weight": 0.08,
        "population_weight": 0.35,
        "base_risk_low": 10,
        "base_risk_moderate": 25,
        "base_risk_high": 40,
        "base_risk_severe": 65,
        "hi_threshold_moderate": 27,
        "hi_threshold_high": 32,
        "hi_threshold_severe": 41,
        "wbgt_threshold_moderate": 25,
        "wbgt_threshold_high": 28,
        "wbgt_threshold_severe": 31,
    }

    @classmethod
    def thresholds_from_config(cls, rows) -> dict:
        """Map ThresholdConfig rows (max-per-category from the Admin Panel)
        onto the thermal cutoffs the scorer uses.

        Admin stores: heat_index.low_threshold = max HI for Low, so Moderate
        begins where Low ends, High where Moderate ends, Severe where High ends.
        Rows with missing/zero values fall back to DEFAULT_COEFFICIENTS."""
        overrides = {}
        by_type = {getattr(r, "config_type", None): r for r in rows}
        for ctype, prefix in (("heat_index", "hi"), ("wbgt", "wbgt")):
            row = by_type.get(ctype)
            if not row:
                continue
            for admin_field, key in (
                ("low_threshold", f"{prefix}_threshold_moderate"),
                ("moderate_threshold", f"{prefix}_threshold_high"),
                ("high_threshold", f"{prefix}_threshold_severe"),
            ):
                v = getattr(row, admin_field, None)
                if v is not None and v > 0:
                    overrides[key] = float(v)
        return overrides

    @classmethod
    def calculate_risk(cls, heat_index: float, wbgt: float, elderly_percent: float, outdoor_worker_density: float,
                       temperature_c: float | None = None, humidity: float | None = None,
                       wind_speed: float = 5.0, solar_radiation: float = 500.0,
                       total_population: int | None = None,
                       thresholds: dict | None = None):
        base_risk = cls._base_risk_from_thermal(heat_index, wbgt, thresholds)
        demographic_multiplier = 1 + (elderly_percent / 100 * cls.DEFAULT_COEFFICIENTS["elderly_weight"]) + (
            outdoor_worker_density * cls.DEFAULT_COEFFICIENTS["outdoor_worker_weight"]
        )
        # Population exposure: denser wards carry higher absolute heat-health risk.
        if total_population:
            demographic_multiplier += min(total_population / 2_000_000, 1.0) * cls.DEFAULT_COEFFICIENTS["population_weight"]
        final_score = min(base_risk * demographic_multiplier, 100)
        anomaly_score = None
        if cls.USE_ML_ANOMALY and temperature_c is not None and humidity is not None:
            try:
                _, anomaly_score = _ml_anomaly(temperature_c, humidity, wind_speed, solar_radiation)
                anomaly = float(anomaly_score)
                # Only blend when the anomaly is actually elevated — a normal
                # reading (0) must never haircut the thermal score.
                if anomaly > 0:
                    final_score = min(final_score * 0.9 + anomaly * 0.1, 100)
            except Exception:
                anomaly_score = None
        risk_category = cls._category(final_score)
        return {
            "risk_category": risk_category,
            "final_score": round(final_score, 1),
            "base_risk": round(base_risk, 1),
            "demographic_multiplier": round(demographic_multiplier, 2),
            "anomaly_score": round(float(anomaly_score), 1) if anomaly_score is not None else None,
            "ml_model_path": cls.MODEL_PATH,
        }

    @classmethod
    def _base_risk_from_thermal(cls, heat_index: float, wbgt: float, thresholds: dict | None = None):
        t = {**cls.DEFAULT_COEFFICIENTS, **(thresholds or {})}
        if heat_index is None and wbgt is None:
            return 10
        hi_mod = t["hi_threshold_moderate"]
        hi_high = t["hi_threshold_high"]
        hi_sev = t["hi_threshold_severe"]
        wb_mod = t["wbgt_threshold_moderate"]
        wb_high = t["wbgt_threshold_high"]
        wb_sev = t["wbgt_threshold_severe"]
        hi_risk = 10
        wb_risk = 10
        if heat_index:
            if heat_index >= hi_sev: hi_risk = 65 + (heat_index - hi_sev) * 1.5
            elif heat_index >= hi_high: hi_risk = 40 + (heat_index - hi_high) * 2.78
            elif heat_index >= hi_mod: hi_risk = 25 + (heat_index - hi_mod) * 3.0
        if wbgt:
            if wbgt >= wb_sev: wb_risk = 65 + (wbgt - wb_sev) * 2.0
            elif wbgt >= wb_high: wb_risk = 40 + (wbgt - wb_high) * 3.33
            elif wbgt >= wb_mod: wb_risk = 25 + (wbgt - wb_mod) * 3.0
        return max(hi_risk, wb_risk)

    @staticmethod
    def _category(score: float):
        if score < 30: return "LOW"
        elif score < 50: return "MODERATE"
        elif score < 75: return "HIGH"
        else: return "SEVERE"