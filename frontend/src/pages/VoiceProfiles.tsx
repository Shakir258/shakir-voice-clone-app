import { useState } from "react";
import { VoiceRecorder } from "../components/VoiceRecorder";
import { VoiceProfileCard } from "../components/VoiceProfileCard";
import { LoadingState } from "../components/LoadingState";
import { ErrorMessage } from "../components/ErrorMessage";
import { useVoices } from "../hooks/useVoices";
import { createVoice, deleteVoice, recomputeVoice, renameVoice } from "../services/voiceApi";
import { ApiError } from "../types/api";

export function VoiceProfiles() {
  const { voices, loading, error, refresh } = useVoices();
  const [pendingBlob, setPendingBlob] = useState<{ blob: Blob; filename: string } | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  async function handleSave() {
    if (!pendingBlob || !name.trim()) return;
    setSaving(true);
    setSaveError(null);
    try {
      await createVoice(name.trim(), pendingBlob.blob, pendingBlob.filename);
      setPendingBlob(null);
      setName("");
      refresh();
    } catch (err) {
      setSaveError(
        err instanceof ApiError ? err.message : "Could not save this voice profile."
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="page">
      <h1>Voice Profiles</h1>
      <p className="consent-note">
        This application is intended for voices you own or have permission to use.
      </p>

      <section className="panel">
        <h2>Create a new profile</h2>
        {!pendingBlob ? (
          <VoiceRecorder onReady={(blob, filename) => setPendingBlob({ blob, filename })} />
        ) : (
          <div className="new-profile-form">
            <audio controls src={URL.createObjectURL(pendingBlob.blob)} />
            <input
              placeholder='Name this voice, e.g. "My Voice"'
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
            />
            <div className="recorder-controls">
              <button className="btn btn-secondary" onClick={() => setPendingBlob(null)}>
                Discard
              </button>
              <button className="btn btn-primary" disabled={!name.trim() || saving} onClick={handleSave}>
                {saving ? "Processing…" : "Save profile"}
              </button>
            </div>
            <ErrorMessage message={saveError} />
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Your voice profiles</h2>
        {loading ? (
          <LoadingState />
        ) : (
          <>
            <ErrorMessage message={error} />
            {voices.length === 0 ? (
              <p className="empty-hint">No voice profiles yet. Create one above.</p>
            ) : (
              <div className="voice-profile-grid">
                {voices.map((v) => (
                  <VoiceProfileCard
                    key={v.id}
                    voice={v}
                    onRename={async (id, newName) => {
                      await renameVoice(id, newName);
                      refresh();
                    }}
                    onDelete={async (id) => {
                      await deleteVoice(id);
                      refresh();
                    }}
                    onRecompute={async (id) => {
                      await recomputeVoice(id);
                      refresh();
                    }}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}
