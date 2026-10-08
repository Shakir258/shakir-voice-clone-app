import { useState } from "react";
import type { VoiceProfile } from "../types/voice";

interface Props {
  voice: VoiceProfile;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onRecompute: (id: string) => Promise<void>;
}

export function VoiceProfileCard({ voice, onRename, onDelete, onRecompute }: Props) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(voice.name);
  const [busy, setBusy] = useState(false);

  async function save() {
    if (!name.trim()) return;
    setBusy(true);
    await onRename(voice.id, name.trim());
    setBusy(false);
    setEditing(false);
  }

  return (
    <div className="voice-profile-card">
      <div className="voice-profile-card-header">
        {editing ? (
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
            autoFocus
          />
        ) : (
          <h3>{voice.name}</h3>
        )}
        <span className={`ready-badge ${voice.is_preset ? "ready" : voice.ready ? "ready" : "not-ready"}`}>
          {voice.is_preset ? "Studio Preset" : voice.ready ? "Ready" : "Needs recompute"}
        </span>
      </div>

      <p className="voice-profile-meta">
        {voice.is_preset
          ? "Pre-installed high quality neural voice"
          : `Created ${new Date(voice.created_at).toLocaleString()}${
              voice.duration_seconds != null ? ` · ${voice.duration_seconds.toFixed(1)}s reference` : ""
            }`}
      </p>

      {!voice.is_preset && (
        <div className="voice-profile-actions">
          {editing ? (
            <>
              <button className="btn btn-primary" disabled={busy} onClick={save}>
                Save
              </button>
              <button className="btn btn-secondary" onClick={() => setEditing(false)}>
                Cancel
              </button>
            </>
          ) : (
            <>
              <button className="btn btn-secondary" onClick={() => setEditing(true)}>
                Rename
              </button>
              <button
                className="btn btn-secondary"
                disabled={busy}
                onClick={async () => {
                  setBusy(true);
                  await onRecompute(voice.id);
                  setBusy(false);
                }}
                title="Recreate this profile's voice data from its saved reference recording."
              >
                Recompute
              </button>
              <button
                className="btn btn-danger"
                disabled={busy}
                onClick={async () => {
                  if (confirm(`Delete voice profile "${voice.name}"? This cannot be undone.`)) {
                    setBusy(true);
                    await onDelete(voice.id);
                  }
                }}
              >
                Delete
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
