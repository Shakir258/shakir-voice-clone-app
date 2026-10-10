import { useState, useMemo } from "react";
import { VoiceRecorder } from "../components/VoiceRecorder";
import { VoiceProfileCard } from "../components/VoiceProfileCard";
import { LoadingState } from "../components/LoadingState";
import { ErrorMessage } from "../components/ErrorMessage";
import { useVoices } from "../hooks/useVoices";
import { createVoice, deleteVoice, recomputeVoice, renameVoice } from "../services/voiceApi";
import { ApiError } from "../types/api";
import { HINDI_CATEGORIES, HINDI_VOICES_BY_ID } from "../data/hindiVoices";

export function VoiceProfiles() {
  const { voices, loading, error, refresh } = useVoices();
  const [pendingBlob, setPendingBlob] = useState<{ blob: Blob; filename: string } | null>(null);
  const [name, setName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Search & Filter States
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedGender, setSelectedGender] = useState<"all" | "male" | "female">("all");
  const [showClonePanel, setShowClonePanel] = useState(false);

  // Filtered Voices Calculation
  const filteredVoices = useMemo(() => {
    return voices.filter((v) => {
      const meta = HINDI_VOICES_BY_ID.get(v.id);
      const voiceName = meta?.name || v.name;
      const category = meta?.category || (v.is_preset ? "Studio" : "Custom Cloned");
      const gender = meta?.gender || v.gender || (voiceName.toLowerCase().includes("female") ? "female" : "male");
      const style = meta?.style || "";
      const desc = meta?.description || "";

      // 1. Search Query
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchesName = voiceName.toLowerCase().includes(query);
        const matchesCategory = category.toLowerCase().includes(query);
        const matchesStyle = style.toLowerCase().includes(query);
        const matchesDesc = desc.toLowerCase().includes(query);
        if (!matchesName && !matchesCategory && !matchesStyle && !matchesDesc) {
          return false;
        }
      }

      // 2. Category Filter
      if (selectedCategory !== "All") {
        if (selectedCategory === "Custom Cloned") {
          if (v.is_preset) return false;
        } else if (category !== selectedCategory) {
          return false;
        }
      }

      // 3. Gender Filter
      if (selectedGender !== "all") {
        if (gender !== selectedGender) return false;
      }

      return true;
    });
  }, [voices, searchTerm, selectedCategory, selectedGender]);

  async function handleSave() {
    if (!pendingBlob || !name.trim()) return;
    setSaving(true);
    setSaveError(null);
    try {
      await createVoice(name.trim(), pendingBlob.blob, pendingBlob.filename);
      setPendingBlob(null);
      setName("");
      setShowClonePanel(false);
      refresh();
    } catch (err) {
      setSaveError(
        err instanceof ApiError ? err.message : "Could not save this voice profile."
      );
    } finally {
      setSaving(false);
    }
  }

  const presetCount = voices.filter((v) => v.is_preset).length;
  const customCount = voices.filter((v) => !v.is_preset).length;

  return (
    <div className="page voice-profiles-page">
      {/* Hero Header */}
      <div className="catalog-hero-header">
        <div className="catalog-hero-content">
          <div className="hero-badge">🎙️ Complete Audio Library</div>
          <h1 className="hero-title">Voice Catalog & Cloner</h1>
          <p className="hero-subtitle">
            Browse {presetCount || "100+"} broadcast-ready Hindi AI voices across news, fiction, commercials & reels — or clone your own voice instantly.
          </p>
        </div>

        <button
          type="button"
          className="btn-toggle-clone"
          onClick={() => setShowClonePanel((prev) => !prev)}
        >
          {showClonePanel ? "✕ Close Cloner" : "➕ Clone Your Voice"}
        </button>
      </div>

      {/* Expandable Voice Clone Studio Panel */}
      {showClonePanel && (
        <section className="panel clone-creator-panel">
          <div className="panel-header-row">
            <div>
              <h2>🎙️ Clone a New Voice Profile</h2>
              <p className="panel-sub-desc">
                Record a 10-30 second clear sample of your speech, or upload an existing audio file (WAV / MP3).
              </p>
            </div>
          </div>

          {!pendingBlob ? (
            <VoiceRecorder onReady={(blob, filename) => setPendingBlob({ blob, filename })} />
          ) : (
            <div className="new-profile-form">
              <audio controls src={URL.createObjectURL(pendingBlob.blob)} className="clone-audio-preview" />
              <div className="clone-name-row">
                <input
                  className="clone-name-input"
                  placeholder='Name your cloned voice (e.g., "My Studio Voice")'
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  maxLength={100}
                />
                <button className="btn btn-secondary" onClick={() => setPendingBlob(null)}>
                  Discard
                </button>
                <button className="btn btn-primary" disabled={!name.trim() || saving} onClick={handleSave}>
                  {saving ? "Synthesizing Profile…" : "Save & Activate"}
                </button>
              </div>
              <ErrorMessage message={saveError} />
            </div>
          )}
        </section>
      )}

      {/* Search and Filters Toolbar */}
      <section className="panel catalog-toolbar-panel">
        <div className="catalog-search-row">
          <div className="search-input-wrapper">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="catalog-search-input"
              placeholder="Search by voice name, category, or style (e.g. Rohit, News, Romance)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                type="button"
                className="btn-clear-search"
                onClick={() => setSearchTerm("")}
              >
                ✕
              </button>
            )}
          </div>

          {/* Gender Filter Segment */}
          <div className="gender-toggle-group">
            <button
              type="button"
              className={`gender-filter-btn ${selectedGender === "all" ? "active" : ""}`}
              onClick={() => setSelectedGender("all")}
            >
              All Genders
            </button>
            <button
              type="button"
              className={`gender-filter-btn ${selectedGender === "male" ? "active" : ""}`}
              onClick={() => setSelectedGender("male")}
            >
              👨 Male
            </button>
            <button
              type="button"
              className={`gender-filter-btn ${selectedGender === "female" ? "active" : ""}`}
              onClick={() => setSelectedGender("female")}
            >
              👩 Female
            </button>
          </div>
        </div>

        {/* Category Filter Chips */}
        <div className="catalog-categories-bar">
          <span className="categories-label">Categories:</span>
          <div className="category-chips-list">
            {HINDI_CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`category-chip ${selectedCategory === cat ? "active" : ""}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
            {customCount > 0 && (
              <button
                type="button"
                className={`category-chip ${selectedCategory === "Custom Cloned" ? "active" : ""}`}
                onClick={() => setSelectedCategory("Custom Cloned")}
              >
                ✨ Custom Cloned ({customCount})
              </button>
            )}
          </div>
        </div>

        <div className="catalog-counter-bar">
          <span>
            Showing <strong>{filteredVoices.length}</strong> of {voices.length} voice profiles
          </span>
          {searchTerm && (
            <span className="search-badge">Filtered by: "{searchTerm}"</span>
          )}
        </div>
      </section>

      {/* Voices Grid */}
      <section className="catalog-grid-section">
        {loading ? (
          <LoadingState label="Loading 100+ Hindi neural voices…" />
        ) : (
          <>
            <ErrorMessage message={error} />
            {filteredVoices.length === 0 ? (
              <div className="empty-catalog-box">
                <span className="empty-icon">🎙️</span>
                <h3>No voices matched your filters</h3>
                <p>Try clearing your search term or switching to another category.</p>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setSearchTerm("");
                    setSelectedCategory("All");
                    setSelectedGender("all");
                  }}
                >
                  Reset All Filters
                </button>
              </div>
            ) : (
              <div className="voice-profile-grid">
                {filteredVoices.map((v) => (
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
