import { MapContainer, TileLayer, GeoJSON } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { fetchWardRisk } from "../services/api";
import { getRiskColor, getRiskInfo } from "../utils/riskConfig";

// Mumbai's approximate center — used to point the map at the right city.
const MUMBAI_CENTER = [19.076, 72.8777];
const INITIAL_ZOOM = 11;

/**
 * HeatMap
 * ---------------------------------------------------------------------------
 * Renders Mumbai's wards as a "choropleth" map — a map where each region
 * is filled with a color representing a data value (here: heatwave risk
 * category), plus a click-to-open popup with live HI/WBGT/risk-score
 * detail for that ward.
 *
 * THE CHOROPLETH ALGORITHM, IN PLAIN TERMS:
 * For every ward polygon, `styleWard` below looks up that ward's
 * `riskCategory` in riskConfig.js and returns the matching color — a
 * lookup, not a calculation. Leaflet fills each polygon with whatever
 * color it's given. The selected ward additionally gets a highlighted
 * border so it's clear which one you're looking at in the sidebar.
 *
 * THE POPUP: Leaflet popups render plain HTML, not React components, so
 * `buildPopupHtml()` below returns an HTML string. We bind a "loading"
 * version immediately (so clicking always feels responsive), then fetch
 * the real detail and swap the popup's content in with
 * `layer.setPopupContent()` once it arrives. This does mean the popup and
 * the sidebar (WardDetailPanel.jsx) each fetch the same data
 * independently — a deliberate simplicity trade-off. If you later want to
 * avoid the duplicate network call, lift the fetch into App.jsx and pass
 * the result down to both.
 *
 * Props:
 *   wards            — GeoJSON FeatureCollection (or null while loading),
 *                       fetched once by the parent (App.jsx).
 *   onWardSelect      — called with the clicked ward's GeoJSON feature.
 *   selectedWardId    — id of the currently selected ward, for highlighting.
 */
export default function HeatMap({ wards, onWardSelect, selectedWardId }) {
  /** Decides the fill/border style for one ward polygon. */
  function styleWard(feature) {
    const isSelected = feature.properties.id === selectedWardId;
    return {
      fillColor: getRiskColor(feature.properties.riskCategory),
      fillOpacity: 0.65,
      color: isSelected ? "var(--color-accent)" : "#1B2436",
      weight: isSelected ? 4 : 1,
    };
  }

  /**
   * Attaches interactivity to each ward polygon as it's drawn: a hover
   * tooltip, a click-to-select-and-popup, and a thicker border on hover.
   */
  function onEachWard(feature, layer) {
    const { id, name } = feature.properties;

    layer.bindTooltip(name, { sticky: true });
    layer.bindPopup(buildLoadingHtml(name));

    layer.on({
      mouseover: (e) => e.target.setStyle({ weight: 3 }),
      mouseout: (e) => e.target.setStyle(styleWard(feature)),
      click: () => {
        onWardSelect(feature);
        loadPopupDetail(layer, id, name);
      },
    });
  }

  /** Fetches HI/WBGT/risk score for one ward and updates its open popup. */
  function loadPopupDetail(layer, wardId, wardName) {
    fetchWardRisk(wardId)
      .then((detail) => layer.setPopupContent(buildDetailHtml(wardName, detail)))
      .catch((err) => layer.setPopupContent(buildErrorHtml(wardName, err.message)));
  }

  if (!wards) {
    // App.jsx shows the shared Spinner/ErrorBanner for the wards fetch,
    // so this component just renders nothing until data is ready.
    return null;
  }

  return (
    <MapContainer center={MUMBAI_CENTER} zoom={INITIAL_ZOOM} className="heat-map">
      {/* Free base map tiles — no API key needed, fine for a hackathon demo. */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {/* key forces Leaflet to redraw when filters/selection change data. */}
      <GeoJSON
        key={`${wards.features.length}-${selectedWardId ?? "none"}`}
        data={wards}
        style={styleWard}
        onEachFeature={onEachWard}
      />
    </MapContainer>
  );
}

// ---------------------------------------------------------------------------
// Popup HTML builders. Plain strings (not JSX) because Leaflet popups are
// not React-rendered — see the comment above buildPopupHtml usage.
// Reuses the same CSS classes as the sidebar panel (risk-badge, ward-stat,
// etc. — see App.css) so the popup looks consistent with the rest of the
// app for free.
// ---------------------------------------------------------------------------

function buildLoadingHtml(wardName) {
  return `<div class="popup-body"><h3>${wardName}</h3><div class="spinner-row"><span class="spinner" aria-hidden="true"></span><span>Loading risk data…</span></div></div>`;
}

function buildErrorHtml(wardName, message) {
  return `<div class="popup-body"><h3>${wardName}</h3><p class="popup-error">Couldn't load risk data: ${message}</p></div>`;
}

function buildDetailHtml(wardName, detail) {
  const riskInfo = getRiskInfo(detail.riskCategory);
  return `
    <div class="popup-body">
      <h3>${wardName}</h3>
      <span class="risk-badge" style="background-color:${riskInfo.color}">${riskInfo.label} risk</span>
      <dl class="ward-stats">
        <div class="ward-stat"><dt>Heat Index</dt><dd>${detail.heatIndexC}°C</dd></div>
        <div class="ward-stat"><dt>WBGT</dt><dd>${detail.wbgtC}°C</dd></div>
        <div class="ward-stat"><dt>Risk Score</dt><dd>${detail.riskScore} / 100</dd></div>
      </dl>
    </div>
  `;
}
