import React, { useEffect, useState } from "react";
import { StatusIndicator } from "../components/StatusIndicator";
import { VoiceProfileSelector } from "../components/VoiceProfileSelector";
import { TextEditor } from "../components/TextEditor";
import { LoadingState } from "../components/LoadingState";
import { ErrorMessage } from "../components/ErrorMessage";
import { AudioPlayer } from "../components/AudioPlayer";
import { GenerationHistory } from "../components/GenerationHistory";
import { useBackendHealth } from "../hooks/useBackendHealth";
import { useVoices } from "../hooks/useVoices";
import { useGeneration } from "../hooks/useGeneration";
import { listGenerations, deleteGeneration } from "../services/generationApi";
import { apiUrl } from "../services/api";
import type { GenerationRecord } from "../types/generation";

const MAX_CHARS = 5000;

const HINDI_SAMPLE_PROMPTS = [
  {
    label: "📺 Prime Time News",
    text: "नमस्कार, आज के मुख्य समाचारों के साथ मैं। देश और दुनिया की तमाम बड़ी ख़बरों पर एक नज़र। आर्थिक मोर्चे पर आज भारत ने एक और ऐतिहासिक उपलब्धि हासिल की है।",
  },
  {
    label: "📖 Kahani / Story",
    text: "एक समय की बात है, विंध्याचल की घनी वादियों के बीच बसा था एक सुंदर गाँव। वहाँ रात होते ही चारों ओर सन्नाटा छा जाता था, और केवल हवा की सरसरहाट सुनाई देती थी।",
  },
  {
    label: "🛍️ Festive Ad",
    text: "इस दिवाली, खुशियों का महा-धमाका! पाएँ पूरे अस्सी प्रतिशत तक की भारी छूट सभी इलेक्ट्रॉनिक्स और कपड़ों पर। ऑफ़र सिर्फ़ सीमित समय के लिए उपलब्ध है!",
  },
  {
    label: "🧘 Guided Meditation",
    text: "अपनी आँखें धीरे से बंद करें। एक गहरी, लंबी सांस अंदर लें... और अपने भीतर उठ रहे सारे तनाव को धीरे-धीरे बाहर छोड़ दें। आप पूरी तरह शांत और सुरक्षित हैं।",
  },
  {
    label: "📱 Tech Review",
    text: "तो दोस्तों, आज के इस वीडियो में हम अनबॉक्स करने वाले हैं इस नए 5G फ्लैगशिप स्मार्टफ़ोन को! इसका कैमरा और डिस्प्ले देखकर आप सचमुच दंग रह जाएंगे।",
  },
];

export function Dashboard() {
  const { status, unreachable } = useBackendHealth();
  const { voices, loading: voicesLoading } = useVoices();
  const { generate, generating, error: genError, result } = useGeneration();

  const [voiceId, setVoiceId] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [speed, setSpeed] = useState<number>(1.0);
  const [pitch, setPitch] = useState<number>(0.0);
  const [format, setFormat] = useState<string>("wav");

  const [history, setHistory] = useState<GenerationRecord[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);

  async function refreshHistory() {
    setHistoryLoading(true);
    try {
      setHistory(await listGenerations());
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    refreshHistory();
  }, []);

  useEffect(() => {
    if (result) refreshHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result]);

  useEffect(() => {
    if (!voiceId && voices.length > 0) {
      const firstReady = voices.find((v) => v.ready);
      if (firstReady) setVoiceId(firstReady.id);
    }
  }, [voices, voiceId]);

  const modelReady = status?.status === "ready";
  const canGenerate =
    (modelReady || voices.find((v) => v.id === voiceId)?.is_preset) &&
    voiceId &&
    text.trim().length > 0 &&
    text.length <= MAX_CHARS;

  async function handleGenerate() {
    if (!voiceId) return;
    await generate(voiceId, text, speed, pitch, format);
  }

  async function handleDeleteGeneration(id: string) {
    await deleteGeneration(id);
    refreshHistory();
  }

  return (
    <div className="page dashboard">
      {/* Studio Header */}
      <div className="dashboard-header">
        <div>
          <div className="hero-badge">🇮🇳 100 Professional Hindi AI Voices</div>
          <h1 className="hero-title">Hindi AI Voice Studio</h1>
          <p className="hero-subtitle">
            Broadcast-quality speech synthesis tailored for YouTube, Stories, Reels, News, Ads & Audiobooks.
          </p>
        </div>
        <StatusIndicator status={status} unreachable={unreachable} />
      </div>

      <p className="consent-note">
        All 100 Hindi voices are engineered with legitimate prosody, acoustic conditioning, and clear phonetics.
      </p>

      {/* 1. Voice Selection Panel */}
      <section className="panel voice-selection-panel">
        <div className="panel-header-row">
          <h2>1. Select Voice Profile</h2>
          <span className="panel-counter">100 Profiles Available</span>
        </div>
        {voicesLoading ? (
          <LoadingState label="Loading 100 Hindi voice profiles…" />
        ) : (
          <VoiceProfileSelector voices={voices} selectedId={voiceId} onSelect={setVoiceId} />
        )}
      </section>

      {/* 2. Text Input & Sample Prompts */}
      <section className="panel text-input-panel">
        <div className="panel-header-row">
          <h2>2. Enter Hindi or English Text</h2>
          <div className="prompt-templates-row">
            <span className="templates-label">Quick Prompts:</span>
            {HINDI_SAMPLE_PROMPTS.map((sample) => (
              <button
                key={sample.label}
                type="button"
                className="btn-sample-chip"
                onClick={() => setText(sample.text)}
              >
                {sample.label}
              </button>
            ))}
          </div>
        </div>
        <TextEditor value={text} onChange={setText} maxChars={MAX_CHARS} />
      </section>

      {/* 3. Advanced Voice Controls & Generation */}
      <section className="panel voice-controls-panel">
        <h2>3. Prosody Controls & Audio Settings</h2>
        <div className="controls-grid">
          {/* Speed Slider */}
          <div className="control-card">
            <div className="control-label-row">
              <span className="control-title">Speed / Tempo:</span>
              <span className="control-value">{speed.toFixed(2)}x</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.05"
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="slider"
            />
            <div className="slider-limits">
              <span>0.5x (Slow)</span>
              <button type="button" className="btn-reset-slider" onClick={() => setSpeed(1.0)}>
                Reset
              </button>
              <span>2.0x (Fast)</span>
            </div>
          </div>

          {/* Pitch Slider */}
          <div className="control-card">
            <div className="control-label-row">
              <span className="control-title">Pitch Shift:</span>
              <span className="control-value">
                {pitch > 0 ? `+${pitch}Hz` : `${pitch}Hz`}
              </span>
            </div>
            <input
              type="range"
              min="-20"
              max="20"
              step="1"
              value={pitch}
              onChange={(e) => setPitch(parseFloat(e.target.value))}
              className="slider"
            />
            <div className="slider-limits">
              <span>-20Hz (Deeper)</span>
              <button type="button" className="btn-reset-slider" onClick={() => setPitch(0.0)}>
                Reset
              </button>
              <span>+20Hz (Higher)</span>
            </div>
          </div>

          {/* Output Format */}
          <div className="control-card">
            <div className="control-label-row">
              <span className="control-title">Output Format:</span>
              <span className="control-value">{format.toUpperCase()}</span>
            </div>
            <div className="format-toggle-group">
              <button
                type="button"
                className={`format-btn ${format === "wav" ? "active" : ""}`}
                onClick={() => setFormat("wav")}
              >
                WAV (Lossless 24kHz)
              </button>
              <button
                type="button"
                className={`format-btn ${format === "mp3" ? "active" : ""}`}
                onClick={() => setFormat("mp3")}
              >
                MP3 (Web Compact)
              </button>
            </div>
            <p className="format-note">
              Deterministic audio caching is enabled to eliminate repeated generation time.
            </p>
          </div>
        </div>

        {/* Generate Button Action */}
        <div className="generate-action-row">
          <button
            className="btn btn-primary btn-large btn-generate-hero"
            disabled={!canGenerate || generating}
            onClick={handleGenerate}
          >
            {generating ? (
              <span className="generating-spinner-row">
                <span className="spinner"></span> Synthesizing Speech…
              </span>
            ) : (
              "⚡ Generate Hindi Speech"
            )}
          </button>
        </div>

        {!modelReady && !unreachable && (
          <p className="hint">
            The local neural model stack is warming up ({status?.status ?? "checking"}
            {status?.detail ? `: ${status.detail}` : ""}).
          </p>
        )}
        <ErrorMessage message={genError} />
        {generating && (
          <LoadingState label="Synthesizing natural Hindi speech with neural phonetics and prosody…" />
        )}

        {/* Audio Player Result */}
        {result && !generating && (
          <div className="generation-result-box">
            <div className="result-header">
              <span className="result-title">🎉 Generation Completed</span>
              <span className="result-meta">
                {result.duration_seconds ? `${result.duration_seconds.toFixed(2)}s audio` : ""}{" "}
                · {result.full_text_chars} chars
              </span>
            </div>
            <AudioPlayer src={apiUrl(result.audio_url)} downloadName={`${result.id}.${format}`} />
          </div>
        )}
      </section>

      {/* 4. Generation History */}
      <section className="panel history-panel">
        <div className="panel-header-row">
          <h2>Recent Generations</h2>
          <span className="panel-counter">{history.length} records</span>
        </div>
        {historyLoading ? (
          <LoadingState />
        ) : (
          <GenerationHistory generations={history.slice(0, 5)} onDelete={handleDeleteGeneration} />
        )}
      </section>
    </div>
  );
}
