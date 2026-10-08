import React, { useState } from "react";
import type { VoiceProfile } from "../types/voice";
import { HINDI_VOICES_BY_ID } from "../data/hindiVoices";
import { VoiceStudioModal } from "./VoiceStudioModal";
import { apiUrl } from "../services/api";

interface Props {
  voices: VoiceProfile[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function VoiceProfileSelector({ voices, selectedId, onSelect }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [previewing, setPreviewing] = useState(false);

  if (voices.length === 0) {
    return (
      <p className="empty-hint">
        Loading voice catalog…
      </p>
    );
  }

  // Find currently selected voice
  const selectedVoice = voices.find((v) => v.id === selectedId) || voices[0];
  const hindiMeta = selectedVoice ? HINDI_VOICES_BY_ID.get(selectedVoice.id) : null;

  const displayName = hindiMeta?.name || selectedVoice?.name || "Selected Voice";
  const displayCategory = hindiMeta?.category || (selectedVoice?.is_preset ? "Studio" : "Custom Cloned");
  const displayGender = hindiMeta?.gender || selectedVoice?.gender || (displayName.includes("Female") ? "female" : "male");
  const displayStyle = hindiMeta?.style || selectedVoice?.style || "Natural Neural";
  const displayDesc = hindiMeta?.description || selectedVoice?.description || "High-quality neural speech synthesis voice.";

  const handleQuickPlay = () => {
    if (!selectedVoice) return;
    const audio = new Audio(apiUrl(`/api/voices/${selectedVoice.id}/preview`));
    setPreviewing(true);
    audio.onended = () => setPreviewing(false);
    audio.onerror = () => setPreviewing(false);
    audio.play().catch(() => setPreviewing(false));
  };

  const presetVoices = voices.filter((v) => v.is_preset);
  const clonedVoices = voices.filter((v) => !v.is_preset);

  return (
    <div className="voice-selector-wrapper">
      {/* Active Voice Spotlight Card */}
      <div className="active-voice-card">
        <div className="active-voice-info">
          <div className="active-voice-badges">
            <span className={`gender-badge ${displayGender === "female" ? "female" : "male"}`}>
              {displayGender === "female" ? "👩 Female" : "👨 Male"}
            </span>
            <span className="category-pill">{displayCategory}</span>
            <span className="style-badge">{displayStyle}</span>
          </div>
          <h3 className="active-voice-name">{displayName}</h3>
          <p className="active-voice-desc">{displayDesc}</p>
        </div>

        <div className="active-voice-actions">
          <button
            type="button"
            className={`btn-preview ${previewing ? "active" : ""}`}
            onClick={handleQuickPlay}
            title="Hear sample audio"
          >
            {previewing ? "🔊 Playing..." : "▶ Hear Sample"}
          </button>
          <button
            type="button"
            className="btn btn-primary btn-browse-library"
            onClick={() => setModalOpen(true)}
          >
            🎧 Browse 100 Hindi Voices
          </button>
        </div>
      </div>

      {/* Quick Dropdown Alternative */}
      <div className="quick-select-row">
        <label htmlFor="quick-voice-select" className="quick-select-label">
          Quick Switch:
        </label>
        <select
          id="quick-voice-select"
          className="voice-selector"
          value={selectedId ?? ""}
          onChange={(e) => onSelect(e.target.value)}
        >
          <option value="" disabled>
            Select a voice profile…
          </option>
          {presetVoices.length > 0 && (
            <optgroup label="🌟 100 Studio Hindi Voices">
              {presetVoices.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))}
            </optgroup>
          )}
          {clonedVoices.length > 0 && (
            <optgroup label="🎙️ Your Cloned Voices">
              {clonedVoices.map((v) => (
                <option key={v.id} value={v.id} disabled={!v.ready}>
                  {v.name} {!v.ready ? " (needs recompute)" : ""}
                </option>
              ))}
            </optgroup>
          )}
        </select>
      </div>

      {/* Full Modal Library */}
      <VoiceStudioModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        voices={voices}
        selectedId={selectedId}
        onSelectVoice={onSelect}
      />
    </div>
  );
}
