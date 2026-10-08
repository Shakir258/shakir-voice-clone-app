import React, { useEffect, useMemo, useRef, useState } from "react";
import type { VoiceProfile } from "../types/voice";
import { HINDI_CATEGORIES, HINDI_VOICES_BY_ID } from "../data/hindiVoices";
import { VoiceCard } from "./VoiceCard";
import { apiUrl } from "../services/api";

interface VoiceStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  voices: VoiceProfile[];
  selectedId: string | null;
  onSelectVoice: (id: string) => void;
}

const PAGE_SIZE = 12;
const FAVORITES_STORAGE_KEY = "voice_studio_favorites";
const RECENT_VOICES_STORAGE_KEY = "voice_studio_recent";

export function VoiceStudioModal({
  isOpen,
  onClose,
  voices,
  selectedId,
  onSelectVoice,
}: VoiceStudioModalProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedGender, setSelectedGender] = useState<"all" | "male" | "female">("all");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [onlyFavorites, setOnlyFavorites] = useState(false);
  const [selectedStyleFilter, setSelectedStyleFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);

  // Favorites state (persisted to localStorage)
  const [favorites, setFavorites] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(FAVORITES_STORAGE_KEY);
      return saved ? JSON.parse(saved) : ["hi-male-news-anchor-01", "hi-female-news-anchor-02"];
    } catch {
      return ["hi-male-news-anchor-01", "hi-female-news-anchor-02"];
    }
  });

  // Recently used voices (persisted to localStorage)
  const [recentIds, setRecentIds] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem(RECENT_VOICES_STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Audio Preview State (shared audio element for lazy-loaded audio preview)
  const [playingVoiceId, setPlayingVoiceId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Initialize shared audio element
  useEffect(() => {
    const audio = new Audio();
    audioRef.current = audio;

    audio.onended = () => {
      setPlayingVoiceId(null);
    };

    audio.onerror = () => {
      setPlayingVoiceId(null);
    };

    return () => {
      audio.pause();
      audio.src = "";
    };
  }, []);

  // Stop audio on modal close
  useEffect(() => {
    if (!isOpen && audioRef.current) {
      audioRef.current.pause();
      setPlayingVoiceId(null);
    }
  }, [isOpen]);

  const toggleFavorite = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setFavorites((prev) => {
      const next = prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id];
      try {
        localStorage.setItem(FAVORITES_STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  };

  const handleTogglePlay = (voiceId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!audioRef.current) return;

    if (playingVoiceId === voiceId) {
      audioRef.current.pause();
      setPlayingVoiceId(null);
    } else {
      audioRef.current.pause();
      // Lazy load preview audio url on demand
      const previewUrl = apiUrl(`/api/voices/${voiceId}/preview`);
      audioRef.current.src = previewUrl;
      audioRef.current
        .play()
        .then(() => {
          setPlayingVoiceId(voiceId);
        })
        .catch(() => {
          setPlayingVoiceId(null);
        });
    }
  };

  const handleSelect = (id: string) => {
    onSelectVoice(id);

    // Update recently used
    setRecentIds((prev) => {
      const next = [id, ...prev.filter((item) => item !== id)].slice(0, 5);
      try {
        localStorage.setItem(RECENT_VOICES_STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });

    onClose();
  };

  // Merge full Hindi profile metadata if backend voice lacks rich fields
  const enrichedVoices = useMemo(() => {
    return voices.map((v) => {
      const hindiMeta = HINDI_VOICES_BY_ID.get(v.id);
      if (hindiMeta) {
        return {
          ...v,
          gender: hindiMeta.gender,
          category: hindiMeta.category,
          style: hindiMeta.style,
          description: hindiMeta.description,
          tags: hindiMeta.tags,
          preview_text: hindiMeta.preview_text,
          is_preset: true,
        };
      }
      return v;
    });
  }, [voices]);

  // Extract all distinct style tags
  const distinctStyles = useMemo(() => {
    const set = new Set<string>();
    enrichedVoices.forEach((v) => {
      if (v.style) set.add(v.style);
    });
    return Array.from(set).sort();
  }, [enrichedVoices]);

  // Filter voices
  const filteredVoices = useMemo(() => {
    return enrichedVoices.filter((v) => {
      // 1. Search term
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase().trim();
        const matchesName = v.name.toLowerCase().includes(query);
        const matchesDesc = (v.description || "").toLowerCase().includes(query);
        const matchesCat = (v.category || "").toLowerCase().includes(query);
        const matchesStyle = (v.style || "").toLowerCase().includes(query);
        const matchesTags = (v.tags || []).some((t) => t.toLowerCase().includes(query));
        if (!matchesName && !matchesDesc && !matchesCat && !matchesStyle && !matchesTags) {
          return false;
        }
      }

      // 2. Favorites only
      if (onlyFavorites && !favorites.includes(v.id)) {
        return false;
      }

      // 3. Gender
      if (selectedGender !== "all") {
        if (v.gender !== selectedGender) return false;
      }

      // 4. Category
      if (selectedCategory !== "All") {
        if (v.category !== selectedCategory) return false;
      }

      // 5. Style
      if (selectedStyleFilter !== "all") {
        if (v.style !== selectedStyleFilter) return false;
      }

      return true;
    });
  }, [
    enrichedVoices,
    searchTerm,
    onlyFavorites,
    favorites,
    selectedGender,
    selectedCategory,
    selectedStyleFilter,
  ]);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedGender, selectedCategory, onlyFavorites, selectedStyleFilter]);

  // Paginated slices
  const totalPages = Math.ceil(filteredVoices.length / PAGE_SIZE) || 1;
  const paginatedVoices = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredVoices.slice(start, start + PAGE_SIZE);
  }, [filteredVoices, currentPage]);

  // Recently used voices list
  const recentVoices = useMemo(() => {
    return recentIds
      .map((id) => enrichedVoices.find((v) => v.id === id))
      .filter((v): v is VoiceProfile => Boolean(v));
  }, [recentIds, enrichedVoices]);

  if (!isOpen) return null;

  return (
    <div className="voice-modal-backdrop" onClick={onClose}>
      <div className="voice-modal-container" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="voice-modal-header">
          <div className="header-titles">
            <h2>🎙️ Professional Hindi Voice Studio</h2>
            <p className="subtitle">
              Explore 100 studio-grade Hindi voices with distinct emotional tones, pacing, and
              acoustics.
            </p>
          </div>
          <button type="button" className="close-modal-btn" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        {/* Recently Used Voices Shelf */}
        {recentVoices.length > 0 && !searchTerm && selectedCategory === "All" && (
          <div className="recent-voices-shelf">
            <span className="shelf-label">⚡ Recently Used:</span>
            <div className="recent-pills-list">
              {recentVoices.map((rv) => (
                <button
                  key={rv.id}
                  type="button"
                  className={`recent-pill ${rv.id === selectedId ? "selected" : ""}`}
                  onClick={() => handleSelect(rv.id)}
                >
                  <span className="pill-gender">{rv.gender === "female" ? "👩" : "👨"}</span>
                  <span className="pill-name">{rv.name.split("—")[0].trim()}</span>
                  <span className="pill-cat">{rv.category}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Search & Filter Controls Bar */}
        <div className="voice-controls-bar">
          <div className="search-box">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search 100 voices by name, style, category, or tag (e.g. Rohit, news, deep, horror)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              autoFocus
            />
            {searchTerm && (
              <button
                type="button"
                className="clear-search-btn"
                onClick={() => setSearchTerm("")}
              >
                ✕
              </button>
            )}
          </div>

          <div className="filters-row">
            {/* Gender Filters */}
            <div className="filter-group gender-filters">
              <button
                type="button"
                className={`filter-pill ${selectedGender === "all" ? "active" : ""}`}
                onClick={() => setSelectedGender("all")}
              >
                All Genders
              </button>
              <button
                type="button"
                className={`filter-pill ${selectedGender === "male" ? "active" : ""}`}
                onClick={() => setSelectedGender("male")}
              >
                👨 Male
              </button>
              <button
                type="button"
                className={`filter-pill ${selectedGender === "female" ? "active" : ""}`}
                onClick={() => setSelectedGender("female")}
              >
                👩 Female
              </button>
            </div>

            {/* Favorites Toggle */}
            <button
              type="button"
              className={`filter-pill fav-pill ${onlyFavorites ? "active" : ""}`}
              onClick={() => setOnlyFavorites(!onlyFavorites)}
            >
              ❤️ Favorites ({favorites.length})
            </button>

            {/* Style Dropdown */}
            <div className="style-select-wrapper">
              <select
                value={selectedStyleFilter}
                onChange={(e) => setSelectedStyleFilter(e.target.value)}
                className="style-dropdown"
              >
                <option value="all">All Speaking Styles</option>
                {distinctStyles.map((st) => (
                  <option key={st} value={st}>
                    {st}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Category Tabs Scroll */}
          <div className="category-tabs-scroll">
            {HINDI_CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                className={`category-tab ${selectedCategory === cat ? "active" : ""}`}
                onClick={() => setSelectedCategory(cat)}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Results Counter */}
        <div className="voice-results-bar">
          <span className="results-count">
            Showing <strong>{filteredVoices.length}</strong> Hindi voices
            {selectedCategory !== "All" ? ` in ${selectedCategory}` : ""}
            {selectedGender !== "all" ? ` (${selectedGender})` : ""}
          </span>
          {filteredVoices.length > PAGE_SIZE && (
            <span className="pagination-info">
              Page {currentPage} of {totalPages}
            </span>
          )}
        </div>

        {/* Voices Grid */}
        <div className="voice-grid-scroll-area">
          {filteredVoices.length === 0 ? (
            <div className="no-voices-state">
              <span className="no-voices-icon">🔎</span>
              <h3>No matching voices found</h3>
              <p>Try clearing your search query or choosing a different category filter.</p>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  setSearchTerm("");
                  setSelectedCategory("All");
                  setSelectedGender("all");
                  setOnlyFavorites(false);
                  setSelectedStyleFilter("all");
                }}
              >
                Reset All Filters
              </button>
            </div>
          ) : (
            <div className="voice-cards-grid">
              {paginatedVoices.map((voice) => (
                <VoiceCard
                  key={voice.id}
                  voice={voice}
                  isSelected={voice.id === selectedId}
                  onSelect={() => handleSelect(voice.id)}
                  isFavorite={favorites.includes(voice.id)}
                  onToggleFavorite={(e) => toggleFavorite(voice.id, e)}
                  isPlaying={playingVoiceId === voice.id}
                  onTogglePlay={(e) => handleTogglePlay(voice.id, e)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Pagination Footer */}
        {totalPages > 1 && (
          <div className="voice-modal-pagination">
            <button
              type="button"
              className="page-nav-btn"
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            >
              ← Previous
            </button>

            <div className="page-numbers">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                <button
                  key={pageNum}
                  type="button"
                  className={`page-num-btn ${currentPage === pageNum ? "active" : ""}`}
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </button>
              ))}
            </div>

            <button
              type="button"
              className="page-nav-btn"
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            >
              Next →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
