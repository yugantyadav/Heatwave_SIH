# Risk model service
from app.core.config import settings

class MortalityRiskService:
    DEFAULT_COEFFICIENTS = {
        "elderly_weight": 0.15,
        "outdoor_worker_weight": 0.08,
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
    def calculate_risk(cls, heat_index: float, wbgt: float, elderly_percent: float, outdoor_worker_density: float):
        base_risk = cls._base_risk_from_thermal(heat_index, wbgt)
        demographic_multiplier = 1 + (elderly_percent / 100 * cls.DEFAULT_COEFFICIENTS["elderly_weight"]) + (outdoor_worker_density * cls.DEFAULT_COEFFICIENTS["outdoor_worker_weight"])
        final_score = min(base_risk * demographic_multiplier * 0.5, 100)
        risk_category = cls._category(final_score)
        return {
            "risk_category": risk_category,
            "final_score": round(final_score, 1),
            "base_risk": round(base_risk, 1),
            "demographic_multiplier": round(demographic_multiplier, 2),
        }

    @staticmethod
    def _base_risk_from_thermal(heat_index: float, wbgt: float):
        if heat_index is None and wbgt is None:
            return 10
        hi_risk = 10
        wb_risk = 10
        if heat_index:
            if heat_index >= 41: hi_risk = 65 + (heat_index - 41) * 1.5
            elif heat_index >= 32: hi_risk = 40 + (heat_index - 32) * 2.78
            elif heat_index >= 27: hi_risk = 25 + (heat_index - 27) * 3.0
        if wbgt:
            if wbgt >= 31: wb_risk = 65 + (wbgt - 31) * 2.0
            elif wbgt >= 28: wb_risk = 40 + (wbgt - 28) * 3.33
            elif wbgt >= 25: wb_risk = 25 + (wbgt - 25) * 3.0
        return max(hi_risk, wb_risk)

    @staticmethod
    def _category(score: float):
        if score < 30: return "low"
        elif score < 50: return "moderate"
        elif score < 75: return "high"
        else: return "severe"