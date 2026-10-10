import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import type { VoiceProfile } from "../types/voice";
import { HINDI_VOICES_BY_ID } from "../data/hindiVoices";
import { apiUrl } from "../services/api";

interface Props {
  voice: VoiceProfile;
  onRename: (id: string, name: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  onRecompute: (id: string) => Promise<void>;
}

export function VoiceProfileCard({ voice, onRename, onDelete, onRecompute }: Props) {
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(voice.name);
  const [busy, setBusy] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const hindiMeta = HINDI_VOICES_BY_ID.get(voice.id);
  const displayName = hindiMeta?.name || voice.name;
  const displayCategory = hindiMeta?.category || (voice.is_preset ? "Studio Voice" : "Custom Cloned");
  const displayGender = hindiMeta?.gender || voice.gender || (displayName.toLowerCase().includes("female") ? "female" : "male");
  const displayStyle = hindiMeta?.style || voice.style || "Natural Neural";
  const displayDesc = hindiMeta?.description || voice.description || (voice.is_preset ? "Studio-grade neural voice with natural Hindi articulation." : "Custom cloned voice from audio sample.");

  const togglePreview = () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      return;
    }

    const audioUrl = apiUrl(`/api/voices/${voice.id}/preview`);
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => setIsPlaying(false);
    audio.play().catch(() => setIsPlaying(false));
  };

  const handleUseVoice = () => {
    navigate("/", { state: { voiceId: voice.id } });
  };

  async function save() {
    if (!name.trim()) return;
    setBusy(true);
    await onRename(voice.id, name.trim());
    setBusy(false);
    setEditing(false);
  }

  return (
    <div className={`voice-profile-card luxury-card ${voice.is_preset ? "preset-card" : "custom-card"}`}>
      {/* Card Header & Badges */}
      <div className="voice-card-top">
        <div className="card-badge-row">
          <span className={`gender-badge ${displayGender === "female" ? "female" : "male"}`}>
            {displayGender === "female" ? "👩 Female" : "👨 Male"}
          </span>
          <span className="category-pill">{displayCategory}</span>
          <span className="style-badge">{displayStyle}</span>
        </div>

        <span className={`ready-badge ${voice.is_preset ? "ready" : voice.ready ? "ready" : "not-ready"}`}>
          {voice.is_preset ? "🇮🇳 Studio Preset" : voice.ready ? "✓ Cloned" : "Needs recompute"}
        </span>
      </div>

      {/* Voice Name & Description */}
      <div className="voice-card-body">
        {editing ? (
          <input
            className="rename-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && save()}
            autoFocus
          />
        ) : (
          <h3 className="voice-card-name" title={displayName}>
            {displayName}
          </h3>
        )}

        <p className="voice-card-desc">{displayDesc}</p>
      </div>

      {/* Audio Sample Preview Text */}
      {hindiMeta?.preview_text && (
        <div className="sample-dialogue-quote">
          "{hindiMeta.preview_text}"
        </div>
      )}

      {/* Card Actions Footer */}
      <div className="voice-card-footer">
        <div className="primary-actions-group">
          <button
            type="button"
            className={`btn-preview-circle ${isPlaying ? "playing" : ""}`}
            onClick={togglePreview}
            title={isPlaying ? "Stop Sample" : "Play Voice Sample"}
          >
            {isPlaying ? "⏹ Stop" : "▶ Hear Sample"}
          </button>

          <button
            type="button"
            className="btn-use-voice"
            onClick={handleUseVoice}
            title="Use this voice to generate speech"
          >
            ⚡ Use in Studio
          </button>
        </div>

        {!voice.is_preset && (
          <div className="custom-voice-tools">
            {editing ? (
              <>
                <button className="btn-tool-save" disabled={busy} onClick={save}>
                  Save
                </button>
                <button className="btn-tool-cancel" onClick={() => setEditing(false)}>
                  Cancel
                </button>
              </>
            ) : (
              <>
                <button className="btn-tool" onClick={() => setEditing(true)}>
                  Rename
                </button>
                <button
                  className="btn-tool"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    await onRecompute(voice.id);
                    setBusy(false);
                  }}
                  title="Recreate profile"
                >
                  Recompute
                </button>
                <button
                  className="btn-tool danger"
                  disabled={busy}
                  onClick={async () => {
                    if (confirm(`Delete voice profile "${voice.name}"?`)) {
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
    </div>
  );
}
