/**
 * riskConfig.js
 * ---------------------------------------------------------------------------
 * The single source of truth for how a risk category is labeled and
 * colored. Every part of the app that needs a risk color (the map, the
 * legend, the ward detail panel) reads from this one object — so if a
 * teammate wants to change what "Severe" looks like, there's exactly one
 * line to edit, and the map and legend can never fall out of sync.
 *
 * The four categories match the backend's mortality/risk model output
 * described in the plan (section 2, R2's role): Low / Moderate / High /
 * Severe. If R2 changes the category names, update the keys below and
 * everything downstream keeps working.
 */

export const RISK_LEVELS = {
  Low: {
    color: "#4C8C5B", // muted green
    label: "Low",
    description: "Routine conditions. No special precautions needed.",
  },
  Moderate: {
    color: "#C9A23A", // amber
    label: "Moderate",
    description: "Sensitive groups should limit prolonged outdoor exposure.",
  },
  High: {
    color: "#D97B34", // orange
    label: "High",
    description: "Outdoor work should be limited during peak hours.",
  },
  Severe: {
    color: "#B23A2E", // deep red
    label: "Severe",
    description: "Dangerous conditions. Avoid outdoor exposure if possible.",
  },
};

export const RISK_ORDER = ["Low", "Moderate", "High", "Severe"];

// Used when a ward's riskCategory doesn't match any known key above —
// e.g. missing data, or a category name typo from the backend. Rendering
// something visible-but-neutral is safer than a crash or a blank shape.
const FALLBACK_RISK = {
  color: "#9AA3B2", // neutral grey
  label: "Unknown",
  description: "Risk data unavailable for this ward.",
};

/** "HIGH" | "high" | "High" -> "High" (frontend canonical form). */
export function normalizeRiskCategory(value) {
  if (!value) return "Moderate";
  const t = String(value).trim().toLowerCase();
  if (t === "low") return "Low";
  if (t === "moderate") return "Moderate";
  if (t === "high") return "High";
  if (t === "severe") return "Severe";
  return "Moderate";
}

/** Returns the color for a given risk category, with a safe fallback. */
export function getRiskColor(riskCategory) {
  return (RISK_LEVELS[normalizeRiskCategory(riskCategory)] ?? FALLBACK_RISK).color;
}

/** Returns the full { color, label, description } entry for a category. */
export function getRiskInfo(riskCategory) {
  return RISK_LEVELS[normalizeRiskCategory(riskCategory)] ?? FALLBACK_RISK;
}

/** Returns a sortable severity score for summaries and default selection. */
export function getRiskRank(riskCategory) {
  const index = RISK_ORDER.indexOf(normalizeRiskCategory(riskCategory));
  return index === -1 ? -1 : index;
}
