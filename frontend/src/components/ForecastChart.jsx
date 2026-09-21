import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { fetchWardForecast } from "../services/api";
import Spinner from "./Spinner";
import ErrorBanner from "./ErrorBanner";

/**
 * ForecastChart
 * ---------------------------------------------------------------------------
 * Shows the 3-5 day Heat Index forecast for whichever ward is selected,
 * as a line chart (via the Recharts library — chosen because it works
 * declaratively with plain data arrays, which keeps this component
 * readable: you hand it `days` and describe what to draw, and Recharts
 * handles the pixel math).
 *
 * `selectedWard` is a GeoJSON feature (or null if nothing is selected
 * yet) — same shape used by WardDetailPanel. We only need its id/name
 * from `.properties`; the actual forecast numbers are fetched fresh
 * whenever the selected ward changes.
 */
export default function ForecastChart({ selectedWard }) {
  const [forecast, setForecast] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const wardId = selectedWard?.properties.id;

  useEffect(() => {
    if (!wardId) {
      setForecast(null);
      return;
    }

    let isCancelled = false;
    setIsLoading(true);
    setError(null);

    fetchWardForecast(wardId)
      .then((data) => {
        if (!isCancelled) setForecast(data);
      })
      .catch((err) => {
        if (!isCancelled) setError(err.message);
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [wardId]);

  // Re-runs the same fetch — handed to ErrorBanner as the "Try again" action.
  function retry() {
    if (wardId) {
      setError(null);
      setForecast(null);
      // Re-triggering the effect: easiest is to just call the fetch again
      // directly, since the effect above only re-runs when wardId changes.
      setIsLoading(true);
      fetchWardForecast(wardId)
        .then(setForecast)
        .catch((err) => setError(err.message))
        .finally(() => setIsLoading(false));
    }
  }

  return (
    <div className="panel">
      <div className="panel-heading-row">
        <div>
          <span className="section-kicker">Outlook</span>
          <h2 className="panel-title panel-title-inline">5-day forecast</h2>
        </div>
        {forecast?.days?.length > 0 && <span className="count-pill">Heat Index</span>}
      </div>

      {!wardId && <p className="panel-empty">Select a ward to see its forecast.</p>}
      {wardId && isLoading && <Spinner label="Loading forecast…" />}
      {wardId && error && <ErrorBanner message={error} onRetry={retry} />}

      {wardId && !isLoading && !error && forecast && (
        <div className="chart-container">
          <div className="forecast-summary">
            <div><span>Today</span><strong className="tabular-num">{forecast.days[0]?.heatIndexC}°C</strong></div>
            <div><span>Day 5</span><strong className="tabular-num">{forecast.days.at(-1)?.heatIndexC}°C</strong></div>
            <div className="forecast-trend"><span aria-hidden="true">↗</span> {forecast.days.at(-1)?.heatIndexC >= forecast.days[0]?.heatIndexC ? "Warming" : "Cooling"}</div>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={forecast.days} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="var(--color-text-muted)" />
              <YAxis
                tick={{ fontSize: 12 }}
                stroke="var(--color-text-muted)"
                unit="°C"
                width={60}
              />
              <Tooltip
                formatter={(value) => [`${value}°C`, "Heat Index"]}
                contentStyle={{ fontSize: 13 }}
              />
              <Line
                type="monotone"
                dataKey="heatIndexC"
                stroke="var(--color-accent)"
                strokeWidth={2}
                dot={{ r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
