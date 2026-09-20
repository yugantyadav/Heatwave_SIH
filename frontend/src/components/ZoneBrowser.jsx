import { getRiskColor, getRiskRank } from "../utils/riskConfig";

/**
 * ZoneBrowser
 * ---------------------------------------------------------------------------
 * Lists every ward grouped under its wider `zone` (South Mumbai / Western
 * Suburbs / Central Suburbs — see mumbaiWardsSample.js), as an alternative
 * to clicking directly on the map. Useful once there are more wards than
 * are easy to find by eye, and it's the same `onWardSelect` callback the
 * map uses, so selecting from here or from the map behaves identically.
 *
 * `wards` is the GeoJSON FeatureCollection from App.jsx (or null while
 * it's still loading, in which case this renders nothing — App.jsx
 * already shows a shared spinner/error for that fetch).
 */
export default function ZoneBrowser({ wards, selectedWardId, onWardSelect }) {
  if (!wards) return null;

  const zoneToWards = groupByZone(wards.features);

  return (
    <div className="panel">
      <div className="panel-heading-row">
        <div>
          <span className="section-kicker">Coverage</span>
          <h2 className="panel-title panel-title-inline">Browse by zone</h2>
        </div>
        <span className="count-pill">{wards.features.length} wards</span>
      </div>
      {wards.features.length === 0 && <p className="panel-empty">No wards match the current filters.</p>}
      <div className="zone-list">
        {Object.entries(zoneToWards).map(([zoneName, wardsInZone]) => (
          <div key={zoneName} className="zone-group">
            <div className="zone-heading"><h3 className="zone-name">{zoneName}</h3><span>{wardsInZone.length}</span></div>
            <div className="zone-ward-buttons">
              {[...wardsInZone].sort((a, b) => getRiskRank(b.properties.riskCategory) - getRiskRank(a.properties.riskCategory)).map((feature) => (
                <button
                  key={feature.properties.id}
                  type="button"
                  className={
                    "zone-ward-button" +
                    (feature.properties.id === selectedWardId ? " zone-ward-button-active" : "")
                  }
                  onClick={() => onWardSelect(feature)}
                >
                  <span className="ward-risk-dot" style={{ backgroundColor: getRiskColor(feature.properties.riskCategory) }} />
                  {feature.properties.name}
                  <span className="ward-button-risk">{feature.properties.riskCategory}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/** Turns a flat list of ward features into { zoneName: [features] }. */
function groupByZone(features) {
  const grouped = {};
  for (const feature of features) {
    const zone = feature.properties.zone ?? "Other";
    if (!grouped[zone]) grouped[zone] = [];
    grouped[zone].push(feature);
  }
  return grouped;
}
