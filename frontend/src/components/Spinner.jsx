/**
 * Spinner
 * ---------------------------------------------------------------------------
 * A small reusable "loading" indicator. Pure CSS (a spinning ring, defined
 * in App.css as .spinner / @keyframes spin) — no image or extra library
 * needed. `label` is shown next to it so screen readers (and humans) know
 * what's loading.
 */
export default function Spinner({ label = "Loading…" }) {
  return (
    <div className="spinner-row" role="status">
      <span className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
