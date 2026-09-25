/**
 * api.js
 * ---------------------------------------------------------------------------
 * Every function the rest of the app uses to get or save data lives here.
 * Nothing else in the app should call fetch() directly.
 *
 * LIVE BACKEND (FastAPI, default http://localhost:8000):
 *   GET  /api/wards/geojson                  -> GeoJSON FeatureCollection
 *   GET  /api/wards/{code}                   -> single ward detail
 *   GET  /api/risk/wards                     -> latest risk per ward
 *   GET  /api/risk/wards/{code}              -> ward risk detail
 *   GET  /api/weather/wards/{code}/current   -> current reading
 *   GET  /api/weather/wards/{code}/forecast  -> { ward_code, current, forecast[] }
 *   GET  /api/config/thresholds              -> [{ config_type, low_... }]
 *   POST /api/config/thresholds              -> upsert (object or list)
 *   GET  /api/config/advisories              -> [{ risk_category, sms_text }]
 *   POST /api/config/advisories              -> upsert (object or list)
 *   POST /api/alerts/trigger                 -> dispatch alert (sandbox)
 *   GET  /api/alerts/                        -> alert log
 *
 * Set VITE_USE_MOCK_DATA=false (see frontend/.env) to use the live backend.
 * Mock mode falls back to src/data/mumbaiWardsSample.js (8 area-specific
 * Mumbai wards at their real centers) so the map works with zero backend.
 */

import { mumbaiWardsSample } from "../data/mumbaiWardsSample";
import { defaultThresholds, defaultAdvisoryTemplates } from "../data/adminDefaults";

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA !== "false";
// Empty means "same origin" — in production the API serves this bundle, so
// requests stay relative and there is no CORS or host mismatch to configure.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
const RISK_CACHE_TTL_MS = 60_000;
const riskRequestCache = new Map();
let advisoryCache = null;

/** Small helper so mock responses feel like a real network call. */
function fakeDelay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Shared fetch wrapper: non-OK -> thrown Error for ErrorBanner handling. */
async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request to ${url} failed (status ${response.status})`);
  }
  return response.json();
}

/** "HIGH" | "high" | "High" -> "High" (frontend canonical form). */
export function normalizeRiskCategory(value) {
  if (!value) return "Moderate";
  const t = String(value).toLowerCase();
  if (t === "low") return "Low";
  if (t === "moderate") return "Moderate";
  if (t === "high") return "High";
  if (t === "severe") return "Severe";
  return "Moderate";
}

/**
 * Parse a backend timestamp for display. The API emits ISO-8601 with an
 * explicit UTC offset, but a value with no offset at all would be read by
 * the browser as *local* time and render hours early — so treat an
 * offset-less string as UTC before formatting.
 */
export function formatTimestamp(value) {
  if (!value) return "";
  const raw = String(value);
  const hasOffset = /(?:Z|[+-]\d{2}:?\d{2})$/.test(raw);
  const date = new Date(hasOffset ? raw : `${raw}Z`);
  if (Number.isNaN(date.getTime())) return raw;
  return date.toLocaleString();
}

// ---------------------------------------------------------------------------
// Wards + risk (map data)
// ---------------------------------------------------------------------------

/**
 * All wards as a GeoJSON FeatureCollection with riskCategory per feature.
 * Live source is GET /api/wards/geojson (real Census polygons + live risk).
 */
export async function fetchWards() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return mumbaiWardsSample;
  }
  const fc = await fetchJson(`${API_BASE_URL}/api/wards/geojson`);
  // Normalize backend riskCategory to Title case for the map.
  return {
    ...fc,
    features: (fc.features ?? []).map((f) => ({
      ...f,
      properties: {
        ...f.properties,
        riskCategory: normalizeRiskCategory(f.properties?.riskCategory),
      },
    })),
  };
}

/** GET /api/wards/{code} — full ward record (powers WardDetailPanel meta). */
export async function fetchWard(wardCode) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    const col = mumbaiWardsSample;
    const ward = col.features.find(
      (f) => String(f.properties.id) === String(wardCode) || String(f.properties.ward_code) === String(wardCode),
    );
    if (!ward) throw new Error(`Unknown ward id: ${wardCode}`);
    return ward;
  }
  return fetchJson(`${API_BASE_URL}/api/wards/${wardCode}`);
}

/**
 * GET /api/risk/wards/{code} — HI/WBGT/risk score + advisory text.
 * Normalized to { wardId, riskCategory, heatIndexC, wbgtC, riskScore,
 * advisory, breakdown } whatever the backend's exact key casing is.
 *
 * Results are cached briefly to collapse the duplicate requests a burst of
 * selection changes causes, but the cache expires: scores are recomputed on
 * the backend every few hours and a permanent cache would pin the panel to
 * whatever was fetched first.
 */
export async function fetchWardRisk(wardId) {
  const cached = riskRequestCache.get(wardId);
  if (cached && Date.now() - cached.at < RISK_CACHE_TTL_MS) {
    return cached.promise;
  }
  if (cached) riskRequestCache.delete(wardId);

  const request = fetchWardRiskUncached(wardId).catch((error) => {
    // A failed request must not poison the cache; retry should be a real retry.
    riskRequestCache.delete(wardId);
    throw error;
  });
  riskRequestCache.set(wardId, { at: Date.now(), promise: request });
  return request;
}

async function fetchWardRiskUncached(wardId) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    const col = mumbaiWardsSample;
    const ward = col.features.find((f) => String(f.properties.id) === String(wardId));
    if (!ward) throw new Error(`Unknown ward id: ${wardId}`);

    const { riskCategory } = ward.properties;
    const sampleByCategory = {
      Low: { heatIndexC: 36, wbgtC: 26, riskScore: 22 },
      Moderate: { heatIndexC: 42, wbgtC: 29, riskScore: 48 },
      High: { heatIndexC: 47, wbgtC: 31, riskScore: 71 },
      Severe: { heatIndexC: 52, wbgtC: 34, riskScore: 93 },
    };

    return {
      wardId,
      riskCategory,
      advisory: defaultAdvisoryTemplates[riskCategory],
      ...(sampleByCategory[riskCategory] ?? sampleByCategory.Moderate),
    };
  }
  const raw = await fetchJson(`${API_BASE_URL}/api/risk/wards/${wardId}`);
  const riskCategory = normalizeRiskCategory(raw.risk_category ?? raw.riskCategory);
  const advisories = await fetchAdvisoryTemplates().catch(() => null);
  return {
    wardId,
    riskCategory,
    heatIndexC: raw.heat_index ?? raw.heatIndexC,
    wbgtC: raw.wbgt ?? raw.wbgtC,
    riskScore: raw.final_score ?? raw.riskScore,
    breakdown: raw.breakdown ?? null,
    advisory: advisories?.[riskCategory] ?? defaultAdvisoryTemplates[riskCategory],
  };
}

/**
 * GET /api/weather/wards/{code}/forecast — 5-day Heat Index outlook.
 * Normalized to { wardId, days: [{ date, heatIndexC }] } for ForecastChart.
 */
export async function fetchWardForecast(wardId) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    const col = mumbaiWardsSample;
    const base = col.features.find((f) => String(f.properties.id) === String(wardId));
    const startHeatIndex = { Low: 34, Moderate: 40, High: 45, Severe: 49 }[base?.properties.riskCategory] ?? 40;

    return {
      wardId,
      days: [0, 1, 2, 3, 4].map((offset) => {
        const heatIndexC = startHeatIndex + offset * 1.5;
        return {
          date: `Day ${offset + 1}`,
          heatIndexC: Math.round(heatIndexC * 10) / 10,
        };
      }),
    };
  }
  const raw = await fetchJson(`${API_BASE_URL}/api/weather/wards/${wardId}/forecast`);
  return {
    wardId,
    days: (raw.forecast ?? []).map((d) => ({
      date: d.date,
      heatIndexC: d.heat_index ?? d.heatIndexC,
    })),
  };
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

/** POST /api/alerts/trigger — dispatch a ward alert (sandbox if no Twilio). */
export async function triggerAlert({ wardCode, riskCategory, message, channel = "sms" }) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return { ward_code: wardCode, alert_channel: channel, alert_status: "sandbox (mock)", message };
  }
  return fetchJson(`${API_BASE_URL}/api/alerts/trigger`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ward_code: String(wardCode), risk_category: String(riskCategory).toUpperCase(), message, channel }),
  });
}

/** GET /api/alerts/ — alert log. */
export async function fetchAlerts() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return { alerts: [] };
  }
  return fetchJson(`${API_BASE_URL}/api/alerts/`);
}

// ---------------------------------------------------------------------------
// Admin panel: thresholds + advisory templates
// ---------------------------------------------------------------------------

function thresholdsListToObject(rows) {
  // Admin leaves Severe blank for "no upper bound"; the API may return null
  // or a legacy 0 — both mean blank, never a valid cutoff.
  const cutoff = (v) => (v === null || v === undefined || v === 0 ? null : v);
  const hi = rows.find((r) => r.config_type === "heat_index") ?? {};
  const wb = rows.find((r) => r.config_type === "wbgt") ?? {};
  return {
    Low: { maxHeatIndexC: cutoff(hi.low_threshold), maxWbgtC: cutoff(wb.low_threshold) },
    Moderate: { maxHeatIndexC: cutoff(hi.moderate_threshold), maxWbgtC: cutoff(wb.moderate_threshold) },
    High: { maxHeatIndexC: cutoff(hi.high_threshold), maxWbgtC: cutoff(wb.high_threshold) },
    Severe: { maxHeatIndexC: cutoff(hi.severe_threshold), maxWbgtC: cutoff(wb.severe_threshold) },
  };
}

/** GET /api/config/thresholds — current HI/WBGT cutoffs per risk category. */
export async function fetchThresholds() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return defaultThresholds;
  }
  const rows = await fetchJson(`${API_BASE_URL}/api/config/thresholds`);
  if (Array.isArray(rows) && rows.length > 0) return thresholdsListToObject(rows);
  return defaultThresholds;
}

/** POST /api/config/thresholds — save edited thresholds (object or list). */
export async function saveThresholds(thresholds) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return thresholds; // pretend the save succeeded and echo it back
  }
  const rows = await fetchJson(`${API_BASE_URL}/api/config/thresholds`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thresholds),
  });
  return Array.isArray(rows) ? thresholdsListToObject(rows) : thresholds;
}

function advisoriesListToObject(rows) {
  const obj = { ...defaultAdvisoryTemplates };
  for (const r of rows ?? []) {
    obj[normalizeRiskCategory(r.risk_category)] = r.sms_text ?? r.whatsapp_text ?? obj[normalizeRiskCategory(r.risk_category)];
  }
  return obj;
}

/** GET /api/config/advisories — current advisory text per risk category. */
export async function fetchAdvisoryTemplates() {
  if (advisoryCache) return advisoryCache;
  if (USE_MOCK_DATA) {
    await fakeDelay();
    advisoryCache = defaultAdvisoryTemplates;
    return advisoryCache;
  }
  const rows = await fetchJson(`${API_BASE_URL}/api/config/advisories`);
  advisoryCache = Array.isArray(rows) && rows.length > 0 ? advisoriesListToObject(rows) : defaultAdvisoryTemplates;
  return advisoryCache;
}

/** POST /api/config/advisories — save edited advisory text. */
export async function saveAdvisoryTemplates(templates) {
  advisoryCache = null; // invalidate so the next read sees the save
  if (USE_MOCK_DATA) {
    await fakeDelay();
    advisoryCache = templates;
    return templates;
  }
  const rows = await fetchJson(`${API_BASE_URL}/api/config/advisories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(templates),
  });
  advisoryCache = Array.isArray(rows) ? advisoriesListToObject(rows) : templates;
  return advisoryCache;
}
