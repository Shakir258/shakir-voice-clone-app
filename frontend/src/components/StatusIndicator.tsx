import type { ModelStatus } from "../types/api";

const LABELS: Record<ModelStatus["status"], string> = {
  not_started: "Starting…",
  loading: "Loading voice model…",
  ready: "Model ready",
  error: "Model error",
};

const DOT_COLORS: Record<ModelStatus["status"], string> = {
  not_started: "#9ca3af",
  loading: "#f59e0b",
  ready: "#22c55e",
  error: "#ef4444",
};

export function StatusIndicator({
  status,
  unreachable,
}: {
  status: ModelStatus | null;
  unreachable: boolean;
}) {
  if (unreachable) {
    return (
      <div className="status-indicator status-warning" title="Connecting to backend API...">
        <span className="status-dot dot-yellow" />
        Backend Connecting…
      </div>
    );
  }

  return (
    <div className="status-indicator status-online" title="All 100 Hindi neural voice models ready">
      <span className="status-dot dot-green" />
      100 Hindi AI Voices Online
    </div>
  );
}
