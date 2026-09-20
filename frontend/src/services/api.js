/**
 * api.js
 * ---------------------------------------------------------------------------
 * Every function the rest of the app uses to get or save data lives here.
 * That's the whole point of this file: nothing else in the app should
 * call fetch() directly. When R3's backend is ready, you only edit this
 * one file — every component that already calls these functions keeps
 * working unchanged.
 *
 * Right now USE_MOCK_DATA is true, so these functions return sample data
 * (from src/data/mumbaiWardsSample.js and adminDefaults.js) after a small
 * fake delay — so loading spinners are visible during development, the
 * same way they'll feel once real network calls are involved.
 *
 * WHEN R3'S BACKEND IS READY:
 * 1. Set USE_MOCK_DATA to false.
 * 2. Set API_BASE_URL to the deployed/local FastAPI URL.
 * 3. Confirm the real routes match the ones used below. The two R3 has
 *    confirmed are GET /api/wards and GET /api/risk/wards/{id} — the
 *    forecast and admin routes are this project's best guess at a
 *    matching naming convention and may need a one-line tweak once R3
 *    publishes them.
 */

import { mumbaiWardsSample } from "../data/mumbaiWardsSample";
import { defaultThresholds, defaultAdvisoryTemplates } from "../data/adminDefaults";

const USE_MOCK_DATA = import.meta.env.VITE_USE_MOCK_DATA !== "false";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const riskRequestCache = new Map();

/** Small helper so mock responses feel like a real network call. */
function fakeDelay(ms = 400) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Shared fetch wrapper: turns a non-OK HTTP response into a thrown Error
 *  with a readable message, so every calling component can handle
 *  failures the same way (catch it, show an ErrorBanner). */
async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Request to ${url} failed (status ${response.status})`);
  }
  return response.json();
}

// ---------------------------------------------------------------------------
// Wards + risk (map data)
// ---------------------------------------------------------------------------

/**
 * GET /api/wards
 * All wards as a GeoJSON FeatureCollection, each carrying just enough
 * data (riskCategory) to color the choropleth map. This is intentionally
 * lightweight — full detail per ward comes from fetchWardRisk() below,
 * fetched only for whichever ward the user actually selects.
 */
export async function fetchWards() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return mumbaiWardsSample;
  }
  return fetchJson(`${API_BASE_URL}/api/wards`);
}

/**
 * GET /api/risk/wards/{id}
 * Full risk detail for one ward — this is what powers both the map
 * popup and the sidebar detail panel: Heat Index, WBGT, a numeric risk
 * score, and the resulting category + advisory text.
 */
export async function fetchWardRisk(wardId) {
  if (riskRequestCache.has(wardId)) {
    return riskRequestCache.get(wardId);
  }

  const request = fetchWardRiskUncached(wardId).catch((error) => {
    // A failed request must not poison the cache; retry should be a real retry.
    riskRequestCache.delete(wardId);
    throw error;
  });
  riskRequestCache.set(wardId, request);
  return request;
}

async function fetchWardRiskUncached(wardId) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    const ward = mumbaiWardsSample.features.find((f) => f.properties.id === wardId);
    if (!ward) throw new Error(`Unknown ward id: ${wardId}`);

    const { riskCategory } = ward.properties;
    // Sample numbers only — real HI/WBGT/riskScore come from R1's
    // pythermalcomfort-based engine and R2's mortality model.
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
  return fetchJson(`${API_BASE_URL}/api/risk/wards/${wardId}`);
}

/**
 * Forecast timeline for one ward (the 3-5 day view). R3 hasn't confirmed
 * this exact path yet — it follows the plan's `GET /forecast/{ward_id}`
 * with the same `/api` prefix the other two confirmed routes use.
 * Update the path here (one line) once R3 publishes the real one.
 */
export async function fetchWardForecast(wardId) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    // A small deterministic "trend" so different wards look different,
    // without needing real forecast data yet.
    const base = mumbaiWardsSample.features.find((f) => f.properties.id === wardId);
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
  return fetchJson(`${API_BASE_URL}/api/forecast/wards/${wardId}`);
}

// ---------------------------------------------------------------------------
// Admin panel: thresholds + advisory templates
// ---------------------------------------------------------------------------

/** GET /api/thresholds — current HI/WBGT cutoffs per risk category. */
export async function fetchThresholds() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return defaultThresholds;
  }
  return fetchJson(`${API_BASE_URL}/api/thresholds`);
}

/**
 * POST /api/thresholds — save edited thresholds. Matches the plan's
 * Day 5-7 backend route list, which lists this exact endpoint.
 */
export async function saveThresholds(thresholds) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return thresholds; // pretend the save succeeded and echo it back
  }
  return fetchJson(`${API_BASE_URL}/api/thresholds`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(thresholds),
  });
}

/**
 * GET /api/advisories — current advisory text per risk category.
 * Not in the plan's confirmed route list yet (only thresholds are) —
 * this is this project's proposed path. Flag it to R3 when you wire up
 * the real backend.
 */
export async function fetchAdvisoryTemplates() {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return defaultAdvisoryTemplates;
  }
  return fetchJson(`${API_BASE_URL}/api/advisories`);
}

/** POST /api/advisories — save edited advisory text. */
export async function saveAdvisoryTemplates(templates) {
  if (USE_MOCK_DATA) {
    await fakeDelay();
    return templates;
  }
  return fetchJson(`${API_BASE_URL}/api/advisories`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(templates),
  });
}
