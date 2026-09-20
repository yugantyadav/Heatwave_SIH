import { getRiskInfo } from "../utils/riskConfig";
import Spinner from "./Spinner";
import ErrorBanner from "./ErrorBanner";

/**
 * Detail view for the ward selected on the map or in the zone browser.
 * Data loading lives in App so the same request can serve this panel and
 * Leaflet's popup through the cached API service.
 */
export default function WardDetailPanel({ selectedWard, detail, isLoading, error, onRetry }) {
  if (!selectedWard) {
    return (
      <div className="panel">
        <h2 className="panel-title">Ward details</h2>
        <p className="panel-empty">Click a ward on the map, or pick one from the zone list below.</p>
      </div>
    );
  }

  const wardName = selectedWard.properties.name;
  const riskInfo = getRiskInfo(detail?.riskCategory ?? selectedWard.properties.riskCategory);

  return (
    <div className="panel ward-detail-panel">
      <div className="panel-heading-row">
        <div>
          <span className="section-kicker">Selected ward</span>
          <h2 className="ward-name">{wardName}</h2>
        </div>
        <span className="ward-code">{selectedWard.properties.id}</span>
      </div>

      {isLoading && <Spinner label="Loading risk data…" />}
      {error && <ErrorBanner message={error} onRetry={onRetry} />}

      {!isLoading && !error && detail && (
        <>
          <div className="risk-summary">
            <span className="risk-badge" style={{ backgroundColor: riskInfo.color }}>{riskInfo.label} risk</span>
            <span className="risk-description">{riskInfo.description}</span>
          </div>

          <div className="metric-grid">
            <div className="ward-stat">
              <dt>Heat Index</dt>
              <dd className="tabular-num">{detail.heatIndexC}°C</dd>
              <span className="metric-caption">Feels like</span>
            </div>
            <div className="ward-stat">
              <dt>WBGT</dt>
              <dd className="tabular-num">{detail.wbgtC}°C</dd>
              <span className="metric-caption">Outdoor stress</span>
            </div>
            <div className="ward-stat">
              <dt>Risk score</dt>
              <dd className="tabular-num">{detail.riskScore}<small> / 100</small></dd>
              <div className="score-track">
                <span style={{ width: `${detail.riskScore}%`, backgroundColor: riskInfo.color }} />
              </div>
            </div>
          </div>

          <div className="advisory-callout">
            <span className="advisory-icon" aria-hidden="true">!</span>
            <div>
              <span className="advisory-label">Recommended action</span>
              <p>{detail.advisory}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}