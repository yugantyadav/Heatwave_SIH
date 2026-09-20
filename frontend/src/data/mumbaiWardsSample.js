/**
 * mumbaiWardsSample.js
 * ---------------------------------------------------------------------------
 * PLACEHOLDER DATA — swap this out once R6 sources the real MCGM ward
 * boundaries (see the plan, section 3: "MCGM open data portal or
 * OpenStreetMap ward boundaries for Mumbai").
 *
 * Real ward boundaries are irregular polygons with dozens of points each.
 * Drawing those by hand isn't practical for a starter file, so each "ward"
 * below is a simple square drawn around that ward's real approximate
 * center point, just big enough to be visible and clickable on the map.
 *
 * WHY THIS SHAPE STILL WORKS FOR DEVELOPMENT:
 * This file follows the exact structure a real GeoJSON file uses
 * (FeatureCollection -> Features -> geometry + properties). Leaflet doesn't
 * care whether the polygon is a hand-drawn square or a real ward outline —
 * it just draws whatever coordinates it's given. So you can build and test
 * every other part of the map (coloring, popups, zone browsing) against
 * this file today, and later swap in the real GeoJSON without changing
 * any other code — as long as the replacement file keeps the same
 * `properties` fields used below (id, name, zone, riskCategory).
 *
 * ZONES:
 * Each ward also carries a `zone` — a wider grouping (South Mumbai /
 * Western Suburbs / Central Suburbs) used by the sidebar's "Browse by
 * Zone" list (see ZoneBrowser.jsx) so the wards aren't just a flat list.
 * This mirrors how MCGM itself groups its 24 wards into these broader
 * regions.
 *
 * HOW TO SWAP IN THE REAL DATA LATER:
 * 1. Get the real ward GeoJSON (MCGM portal / OpenStreetMap export).
 * 2. Make sure each feature's `properties` includes at least: id, name, zone.
 * 3. Merge in live risk data from the backend (see services/api.js)
 *    instead of hardcoding riskCategory here.
 * 4. Replace the export below — nothing else needs to change.
 */

const WARD_DEFINITIONS = [
  { id: "A", name: "Colaba", zone: "South Mumbai", center: [18.9067, 72.8147], riskCategory: "Moderate" },
  { id: "G-N", name: "Dadar", zone: "Central Suburbs", center: [19.0176, 72.8438], riskCategory: "High" },
  { id: "H-W", name: "Bandra West", zone: "Western Suburbs", center: [19.0596, 72.8295], riskCategory: "High" },
  { id: "K-W", name: "Andheri West", zone: "Western Suburbs", center: [19.1136, 72.8697], riskCategory: "Severe" },
  { id: "P-N", name: "Malad", zone: "Western Suburbs", center: [19.1863, 72.8489], riskCategory: "Moderate" },
  { id: "R-C", name: "Borivali", zone: "Western Suburbs", center: [19.2307, 72.8567], riskCategory: "Low" },
  { id: "L", name: "Kurla", zone: "Central Suburbs", center: [19.0728, 72.8826], riskCategory: "High" },
  { id: "M-W", name: "Chembur", zone: "Central Suburbs", center: [19.0522, 72.8994], riskCategory: "Severe" },
];

export const mumbaiWardsSample = {
  type: "FeatureCollection",
  features: WARD_DEFINITIONS.map(makeWardSquare),
};

/**
 * Builds one square GeoJSON "Polygon" feature centered on a given
 * [lat, lng] point. This is only here so the placeholder wards above stay
 * short and readable — the real ward file won't need this helper, since
 * it will already contain full polygon coordinates.
 *
 * GeoJSON polygons list coordinates as [longitude, latitude] pairs (note:
 * reversed from the usual "lat, lng" order people say out loud), and the
 * ring of points must start and end on the same point to "close the loop".
 */
function makeWardSquare({ id, name, zone, center, riskCategory }) {
  const [lat, lng] = center;
  const halfSize = 0.012; // roughly a ~1.3km-wide square, just for visibility

  const topLeft = [lng - halfSize, lat + halfSize];
  const topRight = [lng + halfSize, lat + halfSize];
  const bottomRight = [lng + halfSize, lat - halfSize];
  const bottomLeft = [lng - halfSize, lat - halfSize];

  return {
    type: "Feature",
    properties: {
      id,
      name,
      zone,
      riskCategory, // one of: "Low" | "Moderate" | "High" | "Severe"
      lastUpdated: new Date().toISOString(),
    },
    geometry: {
      type: "Polygon",
      coordinates: [[topLeft, topRight, bottomRight, bottomLeft, topLeft]],
    },
  };
}
