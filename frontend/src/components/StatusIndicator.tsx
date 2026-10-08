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
      <div className="status-indicator" title="Could not reach the backend at all.">
        <span className="status-dot" style={{ background: "#ef4444" }} />
        Backend unreachable — is it running?
      </div>
    );
  }
  if (!status) {
    return (
      <div className="status-indicator">
        <span className="status-dot" style={{ background: "#9ca3af" }} />
        Checking…
      </div>
    );
  }
  return (
    <div className="status-indicator" title={status.detail ?? undefined}>
      <span className="status-dot" style={{ background: DOT_COLORS[status.status] }} />
      {LABELS[status.status]}
      {status.status === "error" && status.detail ? `: ${status.detail}` : ""}
    </div>
  );
}
