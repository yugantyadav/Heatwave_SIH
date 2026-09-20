import { RISK_LEVELS } from "../utils/riskConfig";

/**
 * RiskLegend
 * ---------------------------------------------------------------------------
 * A static key explaining what each choropleth color means. Reads directly
 * from RISK_LEVELS, so if a teammate edits a color or adds a category in
 * riskConfig.js, this legend updates automatically — nothing to keep in
 * sync by hand.
 */
export default function RiskLegend() {
  return (
    <div className="panel">
      <h2 className="panel-title">Risk Legend</h2>
      <ul className="legend-list">
        {Object.entries(RISK_LEVELS).map(([key, level]) => (
          <li key={key} className="legend-row">
            <span
              className="legend-swatch"
              style={{ backgroundColor: level.color }}
              aria-hidden="true"
            />
            <div>
              <div className="legend-label">{level.label}</div>
              <div className="legend-description">{level.description}</div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
