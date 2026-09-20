import ThresholdEditor from "./ThresholdEditor";
import AdvisoryEditor from "./AdvisoryEditor";

/**
 * AdminPanel
 * ---------------------------------------------------------------------------
 * The "Admin Panel" section from the plan: threshold config viewer/editor
 * + advisory template editor, side by side. Each half manages its own
 * data loading/saving (see ThresholdEditor.jsx / AdvisoryEditor.jsx) —
 * this component is just layout.
 */
export default function AdminPanel() {
  return (
    <div className="admin-panel">
      <div className="panel admin-panel-column">
        <ThresholdEditor />
      </div>
      <div className="panel admin-panel-column">
        <AdvisoryEditor />
      </div>
    </div>
  );
}
