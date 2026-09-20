/**
 * ErrorBanner
 * ---------------------------------------------------------------------------
 * A consistent way to show "something failed" across the app, instead of
 * every component inventing its own error text/styling. `onRetry` is
 * optional — pass it whenever the failed thing can just be re-run (most
 * of our fetches can), and this renders a "Try again" button that calls it.
 */
export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="error-banner" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button type="button" className="error-retry-button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}
