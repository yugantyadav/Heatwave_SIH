import { useEffect, useState } from "react";
import { fetchThresholds, saveThresholds } from "../../services/api";
import { RISK_LEVELS } from "../../utils/riskConfig";
import Spinner from "../Spinner";
import ErrorBanner from "../ErrorBanner";

/**
 * ThresholdEditor
 * ---------------------------------------------------------------------------
 * Lets an admin view and edit the Heat Index / WBGT cutoff that defines
 * each risk category (e.g. "High starts at 45°C"). Loads current values
 * with fetchThresholds(), and POSTs edits back with saveThresholds().
 *
 * State shape: { Low: { maxHeatIndexC, maxWbgtC }, Moderate: {...}, ... }
 * — see src/data/adminDefaults.js for the exact shape and the reasoning
 * behind it.
 */
export default function ThresholdEditor() {
  const [thresholds, setThresholds] = useState(null);
  const [initialThresholds, setInitialThresholds] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null); // "saving" | "saved" | null

  useEffect(() => {
    load();
  }, []);

  function load() {
    setIsLoading(true);
    setError(null);
    fetchThresholds()
      .then((data) => {
        setThresholds(data);
        setInitialThresholds(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }

  /** Updates one field (e.g. Moderate's maxWbgtC) as the admin types. */
  function updateField(category, field, rawValue) {
    const value = rawValue === "" ? null : Number(rawValue);
    setValidationError(null);
    setThresholds((current) => ({
      ...current,
      [category]: { ...current[category], [field]: value },
    }));
  }

  function handleSave() {
    const values = Object.values(thresholds);
    const hasInvalidValue = values.some((threshold) =>
      ["maxHeatIndexC", "maxWbgtC"].some((field) => threshold[field] !== null && (!Number.isFinite(threshold[field]) || threshold[field] <= 0)),
    );
    if (hasInvalidValue) {
      setValidationError("Use positive numbers for thresholds, or leave Severe blank for no upper bound.");
      return;
    }
    setValidationError(null);
    setSaveStatus("saving");
    saveThresholds(thresholds)
      .then(() => {
        setInitialThresholds(thresholds);
        setSaveStatus("saved");
        // Clear the "Saved" confirmation after a couple of seconds.
        setTimeout(() => setSaveStatus(null), 2000);
      })
      .catch((err) => setError(err.message));
  }

  if (isLoading) return <Spinner label="Loading thresholds…" />;
  if (error) return <ErrorBanner message={error} onRetry={load} />;

  return (
    <div className="admin-section">
      <h3 className="admin-section-title">Alert Thresholds</h3>
      <p className="admin-section-help">
        The Heat Index / WBGT value at which each risk category begins. Leave a field blank for
        "Severe" to mean "no upper bound".
      </p>
      {validationError && <div className="inline-validation">{validationError}</div>}

      <table className="threshold-table">
        <thead>
          <tr>
            <th>Category</th>
            <th>Max Heat Index (°C)</th>
            <th>Max WBGT (°C)</th>
          </tr>
        </thead>
        <tbody>
          {Object.keys(RISK_LEVELS).map((category) => (
            <tr key={category}>
              <td>
                <span
                  className="legend-swatch"
                  style={{ backgroundColor: RISK_LEVELS[category].color }}
                  aria-hidden="true"
                />
                {category}
              </td>
              <td>
                <input
                  type="number"
                  className="threshold-input"
                  value={thresholds[category].maxHeatIndexC ?? ""}
                  placeholder="No limit"
                  onChange={(e) => updateField(category, "maxHeatIndexC", e.target.value)}
                />
              </td>
              <td>
                <input
                  type="number"
                  className="threshold-input"
                  value={thresholds[category].maxWbgtC ?? ""}
                  placeholder="No limit"
                  onChange={(e) => updateField(category, "maxWbgtC", e.target.value)}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="admin-save-row">
        <button type="button" className="save-button" onClick={handleSave} disabled={saveStatus === "saving" || JSON.stringify(thresholds) === JSON.stringify(initialThresholds)}>
          {saveStatus === "saving" ? "Saving…" : "Save Thresholds"}
        </button>
        {saveStatus === "saved" && <span className="save-confirmation">✓ Saved</span>}
      </div>
    </div>
  );
}
