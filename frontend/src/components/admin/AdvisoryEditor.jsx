import { useEffect, useState } from "react";
import { fetchAdvisoryTemplates, saveAdvisoryTemplates } from "../../services/api";
import { RISK_LEVELS } from "../../utils/riskConfig";
import Spinner from "../Spinner";
import ErrorBanner from "../ErrorBanner";

/**
 * AdvisoryEditor
 * ---------------------------------------------------------------------------
 * Lets an admin view and edit the advisory message shown to the public
 * for each risk category (the text that appears in the ward popup and
 * detail panel). Mirrors ThresholdEditor.jsx's structure on purpose —
 * same load/edit/save pattern, just editing text instead of numbers.
 *
 * State shape: { Low: "text", Moderate: "text", ... } — one string per
 * risk category, matching src/data/adminDefaults.js.
 */
export default function AdvisoryEditor() {
  const [templates, setTemplates] = useState(null);
  const [initialTemplates, setInitialTemplates] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null); // "saving" | "saved" | null

  useEffect(() => {
    load();
  }, []);

  function load() {
    setIsLoading(true);
    setError(null);
    fetchAdvisoryTemplates()
      .then((data) => {
        setTemplates(data);
        setInitialTemplates(data);
      })
      .catch((err) => setError(err.message))
      .finally(() => setIsLoading(false));
  }

  function updateText(category, text) {
    setTemplates((current) => ({ ...current, [category]: text }));
    setSaveStatus(null);
  }

  function handleSave() {
    setSaveStatus("saving");
    saveAdvisoryTemplates(templates)
      .then(() => {
        setInitialTemplates(templates);
        setSaveStatus("saved");
        setTimeout(() => setSaveStatus(null), 2000);
      })
      .catch((err) => setError(err.message));
  }

  if (isLoading) return <Spinner label="Loading advisory templates…" />;
  if (error) return <ErrorBanner message={error} onRetry={load} />;

  return (
    <div className="admin-section">
      <h3 className="admin-section-title">Advisory Templates</h3>
      <p className="admin-section-help">The message shown to the public for each risk category.</p>

      {Object.keys(RISK_LEVELS).map((category) => (
        <div key={category} className="advisory-field">
          <label className="advisory-label" htmlFor={`advisory-${category}`}>
            <span
              className="legend-swatch"
              style={{ backgroundColor: RISK_LEVELS[category].color }}
              aria-hidden="true"
            />
            {category}
          </label>
          <textarea
            id={`advisory-${category}`}
            className="advisory-textarea"
            rows={2}
            value={templates[category]}
            onChange={(e) => updateText(category, e.target.value)}
          />
        </div>
      ))}

      <div className="admin-save-row">
        <button type="button" className="save-button" onClick={handleSave} disabled={saveStatus === "saving" || JSON.stringify(templates) === JSON.stringify(initialTemplates)}>
          {saveStatus === "saving" ? "Saving…" : "Save Advisories"}
        </button>
        {saveStatus === "saved" && <span className="save-confirmation">Saved</span>}
      </div>
    </div>
  );
}
