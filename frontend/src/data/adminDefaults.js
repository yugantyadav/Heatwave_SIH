/**
 * adminDefaults.js
 * ---------------------------------------------------------------------------
 * Default data for the two things the Admin Panel manages:
 *
 * 1. THRESHOLDS — the Heat Index / WBGT cutoffs that decide which risk
 *    category a ward falls into. These are placeholder round numbers.
 *    R2's mortality/risk model (see the plan, section 2) is the real
 *    source of truth — once that's finalized, replace the numbers below
 *    (or better: stop hardcoding them here at all, and only ever read
 *    them from GET /api/thresholds once the backend serves real ones).
 *
 * 2. ADVISORY TEMPLATES — the public-facing advice text shown for each
 *    risk category (e.g. in the ward popup and detail panel). Separate
 *    from riskConfig.js's `description` field on purpose: riskConfig's
 *    text is a short internal label, while these are the longer,
 *    editable messages meant to go out to the public/officials, which is
 *    exactly what a non-engineer would use the Admin Panel to tweak.
 */

export const defaultThresholds = {
  Low: { maxHeatIndexC: 39, maxWbgtC: 27 },
  Moderate: { maxHeatIndexC: 44, maxWbgtC: 30 },
  High: { maxHeatIndexC: 49, maxWbgtC: 32 },
  Severe: { maxHeatIndexC: null, maxWbgtC: null }, // null = "and above"
};

export const defaultAdvisoryTemplates = {
  Low: "Routine conditions. No special precautions needed.",
  Moderate: "Sensitive groups (elderly, young children, outdoor workers) should limit prolonged sun exposure between 12 PM and 4 PM.",
  High: "Outdoor work should be rescheduled outside peak hours. Ensure hydration stations are active at outdoor worksites.",
  Severe: "Dangerous conditions. Avoid all non-essential outdoor exposure. Activate ward-level heat action plan and cooling shelters.",
};
