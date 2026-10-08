import React from "react";
import type { VoiceProfile } from "../types/voice";

interface VoiceCardProps {
  voice: VoiceProfile;
  isSelected: boolean;
  onSelect: () => void;
  isFavorite: boolean;
  onToggleFavorite: (e: React.MouseEvent) => void;
  isPlaying: boolean;
  onTogglePlay: (e: React.MouseEvent) => void;
}

export function VoiceCard({
  voice,
  isSelected,
  onSelect,
  isFavorite,
  onToggleFavorite,
  isPlaying,
  onTogglePlay,
}: VoiceCardProps) {
  const isFemale = voice.gender === "female";
  const genderIcon = isFemale ? "👩" : "👨";
  const genderLabel = isFemale ? "Female" : "Male";

  return (
    <div
      className={`voice-studio-card ${isSelected ? "selected" : ""} ${
        isPlaying ? "playing" : ""
      }`}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      <div className="card-top-row">
        <div className="badges-group">
          <span className={`gender-badge ${isFemale ? "female" : "male"}`}>
            <span className="badge-icon">{genderIcon}</span> {genderLabel}
          </span>
          {voice.category && (
            <span className="category-pill">{voice.category}</span>
          )}
        </div>
        <button
          type="button"
          className={`favorite-btn ${isFavorite ? "favorited" : ""}`}
          onClick={onToggleFavorite}
          title={isFavorite ? "Remove from favorites" : "Add to favorites"}
          aria-label={isFavorite ? "Favorited" : "Favorite"}
        >
          {isFavorite ? "❤️" : "🤍"}
        </button>
      </div>

      <div className="card-body">
        <h3 className="voice-name">{voice.name}</h3>

        <div className="voice-meta-tags">
          {voice.style && <span className="style-badge">{voice.style}</span>}
          <span className="lang-badge">Hindi</span>
          {voice.is_preset && <span className="studio-badge">Studio</span>}
        </div>

        <p className="voice-description">
          {voice.description ||
            "Professional, natural Hindi neural voice for studio productions."}
        </p>
      </div>

      <div className="card-footer" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className={`btn-preview ${isPlaying ? "active" : ""}`}
          onClick={onTogglePlay}
          title="Play voice preview"
        >
          {isPlaying ? (
            <>
              <span className="waveform-anim">
                <span className="bar bar-1"></span>
                <span className="bar bar-2"></span>
                <span className="bar bar-3"></span>
              </span>
              <span className="btn-text">Playing</span>
            </>
          ) : (
            <>
              <span className="play-icon">▶</span>
              <span className="btn-text">Preview</span>
            </>
          )}
        </button>

        <button
          type="button"
          className={`btn-select ${isSelected ? "selected" : ""}`}
          onClick={onSelect}
        >
          {isSelected ? "✓ Selected" : "Use Voice"}
        </button>
      </div>
    </div>
  );
}
