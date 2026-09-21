import { useState } from "react";
import { getRiskInfo } from "../utils/riskConfig";
import { triggerAlert } from "../services/api";
import Spinner from "./Spinner";
import ErrorBanner from "./ErrorBanner";

/**
 * Detail view for the ward selected on the map or in the zone browser.
 * Data loading lives in App (GET /api/wards/{id} for `wardMeta`, and
 * GET /api/risk/wards/{id} for `detail`) so the same requests can serve
 * this panel and Leaflet's popup through the cached API service.
 *
 * The "Send alert" button POSTs to /api/alerts/trigger (sandbox when no
 * Twilio credentials are configured) with its own inline
 * loading/error/success states.
 */
export default function WardDetailPanel({ selectedWard, detail, wardMeta, isLoading, error, onRetry }) {
  const [alertStatus, setAlertStatus] = useState(null); // "sending" | "sent" | null
  const [alertError, setAlertError] = useState(null);

  if (!selectedWard) {
    return (
      <div className="panel">
        <h2 className="panel-title">Ward details</h2>
        <p className="panel-empty">Click a ward on the map, or pick one from the zone list below.</p>
      </div>
    );
  }

  const wardName = selectedWard.properties.name ?? wardMeta?.ward_name ?? "Ward";
  const riskInfo = getRiskInfo(detail?.riskCategory ?? selectedWard.properties.riskCategory);
  const population = wardMeta?.total_population ?? selectedWard.properties.total_population;
  const district = wardMeta?.district ?? selectedWard.properties.district;

  async function handleSendAlert() {
    if (!detail) return;
    setAlertStatus("sending");
    setAlertError(null);
    try {
      await triggerAlert({
        wardCode: selectedWard.properties.id,
        riskCategory: detail.riskCategory,
        message: detail.advisory ?? `${detail.riskCategory} heat risk in ${wardName}.`,
        channel: "sms",
      });
      setAlertStatus("sent");
      setTimeout(() => setAlertStatus(null), 3000);
    } catch (err) {
      setAlertStatus(null);
      setAlertError(err.message);
    }
  }

  return (
    <div className="panel ward-detail-panel">
      <div className="panel-heading-row">
        <div>
          <span className="section-kicker">Selected ward</span>
          <h2 className="ward-name">{wardName}</h2>
        </div>
        <span className="ward-code">{selectedWard.properties.id}</span>
      </div>
      {(population || district) && (
        <p className="panel-empty" style={{ marginTop: 0 }}>
          {[district, population ? `${Number(population).toLocaleString("en-IN")} residents` : null]
            .filter(Boolean)
            .join(" · ")}
        </p>
      )}

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

          <div className="admin-save-row">
            <button type="button" className="save-button" onClick={handleSendAlert} disabled={alertStatus === "sending"}>
              {alertStatus === "sending" ? "Sending…" : "Send alert (SMS)"}
            </button>
            {alertStatus === "sent" && <span className="save-confirmation">✓ Alert logged</span>}
          </div>
          {alertError && <ErrorBanner message={alertError} onRetry={handleSendAlert} />}
        </>
      )}
    </div>
  );
}
