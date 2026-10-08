import { StatusIndicator } from "../components/StatusIndicator";
import { useBackendHealth } from "../hooks/useBackendHealth";

export function Settings() {
  const { status, unreachable } = useBackendHealth();

  return (
    <div className="page">
      <h1>Settings</h1>

      <section className="panel">
        <h2>Model status</h2>
        <StatusIndicator status={status} unreachable={unreachable} />
        {status?.detail && <p className="hint">{status.detail}</p>}
        <p className="hint">Device: {status?.device ?? "unknown"}</p>
      </section>

      <section className="panel">
        <h2>Storage locations</h2>
        <p>
          Voice profiles: <code>backend/data/voices/&lt;voice-id&gt;/</code>
          <br />
          Generated audio: <code>backend/data/generated/</code>
          <br />
          Generation history: <code>backend/data/history.json</code>
        </p>
        <p className="hint">
          See <code>CONFIGURATION.md</code> to change any of these paths.
        </p>
      </section>

      <section className="panel">
        <h2>Privacy</h2>
        <p>
          No analytics, no tracking, no third-party voice upload. All processing
          and storage stays on this machine. See README "Privacy" for details on
          what network access is used only for installation vs. runtime.
        </p>
      </section>
    </div>
  );
}
