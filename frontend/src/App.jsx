import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import HeatMap from "./components/HeatMap";
import RiskLegend from "./components/RiskLegend";
import WardDetailPanel from "./components/WardDetailPanel";
import ZoneBrowser from "./components/ZoneBrowser";
import Spinner from "./components/Spinner";
import ErrorBanner from "./components/ErrorBanner";
import { fetchWard, fetchWardRisk, fetchWards, fetchAlerts } from "./services/api";
import { getRiskRank, RISK_ORDER, normalizeRiskCategory, getRiskColor } from "./utils/riskConfig";
import "./App.css";

// recharts (ForecastChart) and the admin workspace only render on demand —
// lazy-loading them keeps the initial dashboard bundle under the 500 kB cap.
const ForecastChart = lazy(() => import("./components/ForecastChart"));
const AdminPanel = lazy(() => import("./components/admin/AdminPanel"));

/**
 * App
 * ---------------------------------------------------------------------------
 * Top-level layout and the one place that fetches the ward list
 * (GET /api/wards) — both the map and the zone browser need it, so it's
 * fetched once here and passed down as a prop, rather than each of them
 * fetching it separately.
 *
 * `selectedWard` (the clicked-or-picked ward, or null) is kept here too,
 * since three different children need it: the map (to highlight it), the
 * detail panel, and the forecast chart. This is "lifting state up" — the
 * standard React pattern for sibling components sharing one piece of data.
 *
 * `activeTab` switches between the two sections the plan calls for:
 * the live map dashboard, and the admin panel.
 */
export default function App() {
  const [wards, setWards] = useState(null);
  const [wardsError, setWardsError] = useState(null);
  const [selectedWard, setSelectedWard] = useState(null);
  const [wardDetail, setWardDetail] = useState(null);
  const [wardDetailError, setWardDetailError] = useState(null);
  const [isWardDetailLoading, setIsWardDetailLoading] = useState(false);
  const [wardMeta, setWardMeta] = useState(null);
  const [activeTab, setActiveTab] = useState("dashboard"); // "dashboard" | "admin"
  const [searchTerm, setSearchTerm] = useState("");
  const [riskFilter, setRiskFilter] = useState("All");
  const [alerts, setAlerts] = useState(null);
  const [alertsError, setAlertsError] = useState(null);

  useEffect(() => {
    loadWards();
    loadAlerts();
    const timer = setInterval(loadAlerts, 30000);
    return () => clearInterval(timer);
  }, []);

  function loadAlerts() {
    fetchAlerts()
      .then((data) => {
        setAlerts(data?.alerts ?? []);
        setAlertsError(null);
      })
      .catch((err) => setAlertsError(err.message));
  }

  function loadWards() {
    setWardsError(null);
    setWards(null);
    setSelectedWard(null);
    fetchWards()
      .then((data) => {
        setWards(data);
        const firstWard = [...data.features].sort(
          (a, b) => getRiskRank(b.properties.riskCategory) - getRiskRank(a.properties.riskCategory),
        )[0];
        setSelectedWard(firstWard ?? null);
      })
      .catch((err) => setWardsError(err.message));
  }

  useEffect(() => {
    const wardId = selectedWard?.properties.id;
    if (!wardId) {
      setWardDetail(null);
      setWardDetailError(null);
      setWardMeta(null);
      return undefined;
    }

    let cancelled = false;
    setIsWardDetailLoading(true);
    setWardDetailError(null);
    // Ward record (GET /api/wards/{id}) enriches the panel with live
    // population/district; risk detail (GET /api/risk/wards/{id}) drives
    // the scores. Both are fetched in parallel for the same selection.
    fetchWard(wardId)
      .then((data) => {
        if (!cancelled) setWardMeta(data);
      })
      .catch(() => {
        if (!cancelled) setWardMeta(null); // geojson props already cover the basics
      });
    fetchWardRisk(wardId)
      .then((data) => {
        if (!cancelled) setWardDetail(data);
      })
      .catch((err) => {
        if (!cancelled) setWardDetailError(err.message);
      })
      .finally(() => {
        if (!cancelled) setIsWardDetailLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedWard]);

  const filteredWards = useMemo(() => {
    if (!wards) return null;
    const normalizedQuery = searchTerm.trim().toLowerCase();
    return {
      ...wards,
      features: wards.features.filter((ward) => {
        const { name, id, zone, riskCategory } = ward.properties;
        const matchesSearch =
          !normalizedQuery ||
          [name, id, zone].some((value) => value?.toLowerCase().includes(normalizedQuery));
        const matchesRisk = riskFilter === "All" || riskCategory === riskFilter;
        return matchesSearch && matchesRisk;
      }),
    };
  }, [wards, searchTerm, riskFilter]);

  const summary = useMemo(() => {
    const features = wards?.features ?? [];
    const countByRisk = RISK_ORDER.reduce((counts, level) => {
      counts[level] = features.filter((ward) => ward.properties.riskCategory === level).length;
      return counts;
    }, {});
    const mostExposed = [...features].sort(
      (a, b) => getRiskRank(b.properties.riskCategory) - getRiskRank(a.properties.riskCategory),
    )[0];
    return {
      total: features.length,
      critical: (countByRisk.High ?? 0) + (countByRisk.Severe ?? 0),
      countByRisk,
      mostExposed,
    };
  }, [wards]);

  function handleWardSelect(ward) {
    setSelectedWard(ward);
    setWardDetailError(null);
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">+</div>
          <div>
            <h1 className="app-title">HeatWatch Mumbai</h1>
            <span className="app-subtitle">Extreme heat early warning system</span>
          </div>
        </div>
        <div className="header-status">
          <span className="live-pill"><span className="live-dot" /> Live model</span>
          <span className="sync-copy">Updated just now</span>
        </div>
        <nav className="tab-bar" aria-label="Dashboard sections">
          <button type="button" className={"tab-button" + (activeTab === "dashboard" ? " tab-button-active" : "")} onClick={() => setActiveTab("dashboard")}>
            <span aria-hidden="true">⌁</span> Live Dashboard
          </button>
          <button type="button" className={"tab-button" + (activeTab === "admin" ? " tab-button-active" : "")} onClick={() => setActiveTab("admin")}>
            <span aria-hidden="true">⚙</span> Admin Panel
          </button>
        </nav>
      </header>

      {activeTab === "dashboard" && (
        <main className="app-main">
          <section className="dashboard-content">
            <div className="page-heading">
              <div>
                <p className="eyebrow">Mumbai municipal operations · Sunday, 20 September 2026</p>
                <h2>Heat risk at a glance</h2>
                <p className="page-heading-copy">Monitor ward-level thermal stress and act before the afternoon peak.</p>
              </div>
              <div className="model-status">
                <span className="status-check">✓</span>
                <div><strong>Model online</strong><span>Forecast horizon · 5 days</span></div>
              </div>
            </div>

            <div className="summary-grid" aria-label="City heat risk summary">
              <div className="summary-card">
                <span className="summary-label">Wards monitored</span>
                <strong className="summary-value tabular-num">{summary.total || "—"}</strong>
                <span className="summary-note">Across Mumbai</span>
              </div>
              <div className="summary-card summary-card-alert">
                <span className="summary-label">High + severe</span>
                <strong className="summary-value tabular-num">{wards ? summary.critical : "—"}</strong>
                <span className="summary-note">Need attention today</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Peak exposure</span>
                <strong className="summary-value summary-value-name">{summary.mostExposed?.properties.name ?? "—"}</strong>
                <span className="summary-note">{summary.mostExposed?.properties.riskCategory ?? "Waiting for data"} risk</span>
              </div>
              <div className="summary-card">
                <span className="summary-label">Action window</span>
                <strong className="summary-value">12–4 PM</strong>
                <span className="summary-note">Tomorrow’s peak hours</span>
              </div>
            </div>

            <div className="map-toolbar">
              <div>
                <span className="section-kicker">Risk map</span>
                <h2 className="map-title">Ward-level thermal stress</h2>
              </div>
              <div className="map-controls">
                <label className="search-field">
                  <span aria-hidden="true">⌕</span>
                  <input value={searchTerm} onChange={(event) => setSearchTerm(event.target.value)} placeholder="Search ward or zone" aria-label="Search ward or zone" />
                </label>
                <label className="filter-field">
                  <span className="sr-only">Filter by risk</span>
                  <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)} aria-label="Filter by risk">
                    <option value="All">All risk levels</option>
                    {RISK_ORDER.slice().reverse().map((level) => <option key={level} value={level}>{level}</option>)}
                  </select>
                </label>
              </div>
            </div>

            <div className="map-wrapper">
            {wardsError && <ErrorBanner message={`Couldn't load wards: ${wardsError}`} onRetry={loadWards} />}
            {!wardsError && !wards && (
              <div className="map-status">
                <Spinner label="Loading ward map…" />
              </div>
            )}
            {!wardsError && wards && (
              <>
                {filteredWards.features.length === 0 && <div className="map-empty">No wards match these filters.</div>}
                <HeatMap wards={filteredWards} onWardSelect={handleWardSelect} selectedWardId={selectedWard?.properties.id} />
              </>
            )}
            </div>
            <div className="map-footnote"><span className="map-footnote-dot" /> Live ward risk layer <span>·</span> Click a ward for details</div>

            <section className="alerts-window" aria-label="Active heat alerts">
              <div className="alerts-window-header">
                <div>
                  <span className="section-kicker">Alert center</span>
                  <h2 className="map-title">Active alerts</h2>
                </div>
                <span className="alerts-count-pill">
                  {alerts ? `${alerts.length} total` : "…"}
                </span>
              </div>
              {alertsError && (
                <div className="alerts-empty alerts-empty-error">Couldn&apos;t load alerts: {alertsError}</div>
              )}
              {!alertsError && !alerts && <div className="alerts-empty">Loading alerts…</div>}
              {!alertsError && alerts && alerts.length === 0 && (
                <div className="alerts-empty">No active alerts. Wards below the High threshold are quiet.</div>
              )}
              {!alertsError && alerts && alerts.length > 0 && (
                <ul className="alerts-list">
                  {alerts.slice(0, 8).map((alert) => {
                    const level = normalizeRiskCategory(alert.triggered_by);
                    return (
                      <li key={alert.id} className="alert-row">
                        <span className="alert-severity-dot" style={{ backgroundColor: getRiskColor(level) }} aria-hidden="true" />
                        <div className="alert-body">
                          <div className="alert-meta">
                            <strong className="alert-ward">Ward {alert.ward_code}</strong>
                            <span className="alert-badge" style={{ backgroundColor: getRiskColor(level) }}>
                              {level}
                            </span>
                            <span className="alert-channel">{alert.alert_channel?.toUpperCase()} · {alert.alert_status}</span>
                          </div>
                          <p className="alert-message">{alert.message}</p>
                          <time className="alert-time" dateTime={alert.sent_at}>
                            {alert.sent_at ? new Date(alert.sent_at).toLocaleString() : ""}
                          </time>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
              {alerts && alerts.length > 8 && (
                <div className="alerts-more">+{alerts.length - 8} more in the log</div>
              )}
            </section>
          </section>

          <aside className="sidebar">
            <WardDetailPanel selectedWard={selectedWard} detail={wardDetail} wardMeta={wardMeta} isLoading={isWardDetailLoading} error={wardDetailError} onRetry={() => selectedWard && handleWardSelect({ ...selectedWard })} />
            <Suspense fallback={<div className="map-status"><Spinner label="Loading forecast…" /></div>}>
              <ForecastChart selectedWard={selectedWard} />
            </Suspense>
            <ZoneBrowser wards={filteredWards} selectedWardId={selectedWard?.properties.id} onWardSelect={handleWardSelect} />
            <RiskLegend />
          </aside>
        </main>
      )}

      {activeTab === "admin" && (
        <main className="app-main app-main-admin">
          <div className="admin-heading">
            <div><p className="eyebrow">Configuration workspace</p><h2>Heat action controls</h2><p>Set the thresholds and public guidance that drive ward-level alerts.</p></div>
            <span className="admin-badge">Admin access</span>
          </div>
          <Suspense fallback={<div className="map-status"><Spinner label="Loading admin panel…" /></div>}>
            <AdminPanel />
          </Suspense>
        </main>
      )}
    </div>
  );
}
