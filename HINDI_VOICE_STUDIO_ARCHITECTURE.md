# 🎙️ Professional Hindi AI Voice Platform Architecture

This document details the architecture, models, licensing, configuration, caching, and deployment instructions for the **100 Professional Hindi AI Voice Platform**.

---

## 1. System Overview & Architecture

```
[ Frontend: React 18 + Vite + TypeScript ]
  │
  ├── VoiceStudioModal (Search, Category Filters, Gender Filters, Favorites, Lazy Preview)
  ├── VoiceProfileSelector (Spotlight Card + Quick Switch)
  ├── Dashboard (Speed Slider, Pitch Offset, Hindi Prompt Templates, WAV/MP3)
  └── AudioPlayer (Lossless 24kHz playback + WAV/MP3 downloads)
       │
       │ HTTP / REST API (JSON + Audio Streams)
       ▼
[ Backend: FastAPI (Python 3.12) ]
  │
  ├── /api/voices                    ── List 100 Hindi voices + custom cloned voices
  ├── /api/voices/{id}/preview       ── Lazy-loaded audio preview with persistent caching
  ├── /api/voices/{id}/generate      ── Full text speech synthesis
  │
  ├── [ Cache Service ]              ── Deterministic SHA-256 hash (text+voice+speed+pitch+format)
  ├── [ Hindi Chunker ]              ── Devanagari punctuation-aware splitter (।, ॥, ., !, ?)
  │
  ├── [ Multi-Engine Orchestrator ]
  │     ├── AI4Bharat Indic Parler-TTS  ── (Apache 2.0) Prompt-conditioned Hindi speech
  │     ├── Piper TTS (hi_IN ONNX)      ── (MIT) Ultra-fast offline CPU synthesis
  │     ├── Neural Studio Fallback      ── High-fidelity studio voice stream
  │     └── OpenVoice V2 Tone Converter ── (MIT) Timbre re-coloring for custom recordings
  │
  └── [ Storage & Data ]
        ├── backend/data/cache/      ── Deterministic audio cache
        ├── backend/data/previews/   ── Pre-rendered voice preview samples
        ├── backend/data/generated/  ── Completed user generations
        └── backend/data/voices/     ── Custom voice embeddings (se.pth)
```

---

## 2. Open-Source Hindi TTS Research & Evaluation

| Model | Repository | License | Commercial Use | Hindi Support | Speakers / Cloning | Quality & Prosody | Hardware | Recommended Use |
|---|---|---|---|---|---|---|---|---|
| **AI4Bharat Indic Parler-TTS** | [ai4bharat/indic-parler-tts](https://huggingface.co/ai4bharat/indic-parler-tts) | **Apache 2.0** | **Permitted** | **Native Hindi** + 21 Indian languages | Prompt-driven dynamic voice generation | ⭐⭐⭐⭐⭐ Highest natural prosody, Devanagari phonetics | 6GB+ GPU recommended; CPU supported | Primary open-source engine for expressive narration |
| **Piper TTS (hi_IN ONNX)** | [rhasspy/piper](https://github.com/rhasspy/piper) | **MIT** | **Permitted** | **Native Hindi** (`hi_IN-rohan`, `hi_IN-priyamvada`, `hi_IN-pratham`) | 3 native Hindi studio speakers | ⭐⭐⭐⭐ Crisp, intelligible | Real-time on CPU (RTF < 0.2x, <100MB RAM) | Lightweight local offline engine for low-spec setups |
| **AI4Bharat IndicF5** | [AI4Bharat/IndicF5](https://github.com/AI4Bharat/IndicF5) | **MIT** | **Permitted** | **Native Hindi** (1,417h Indian speech) | Zero-shot cloning via 3-10s audio | ⭐⭐⭐⭐⭐ Near-human polyglot quality | 8GB+ GPU recommended | Custom Hindi voice cloning from user reference audio |
| **AI4Bharat Indic-TTS** | [AI4Bharat/Indic-TTS](https://github.com/AI4Bharat/Indic-TTS) | **MIT** | **Permitted** | **Native Hindi** | Male & Female acoustic models | ⭐⭐⭐⭐ Clean, traditional acoustic cadence | CPU / GPU | Classical self-hosted Indian language pipeline |
| **Kokoro-82M** | [hexgrad/Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | **Apache 2.0** | **Permitted** | Experimental Hindi (`hf_alpha`, `hm_omega`) | 82M params multi-speaker | ⭐⭐⭐⭐ Smooth, English-accented on complex Hindi | Ultra-fast on CPU | Secondary multilingual backup |
| **Coqui XTTS-v2** | [coqui-ai/XTTS-v2](https://github.com/coqui-ai/TTS) | **CPML** | ❌ **Non-Commercial Only** | Fine-tunes only | Zero-shot voice cloning | High | 6GB+ VRAM | **Not recommended for commercial production** |

---

## 3. The 100 Legitimate Hindi Voice System

The system defines **exactly 100 distinct Hindi voice profiles** in [`backend/app/hindi_voices.py`](file:///c:/Users/HP/Downloads/voice-clone-app/voice-clone-app/backend/app/hindi_voices.py) and [`frontend/src/data/hindiVoices.ts`](file:///c:/Users/HP/Downloads/voice-clone-app/voice-clone-app/frontend/src/data/hindiVoices.ts).

### Content Domains Covered:
1. **News & Broadcast (1–8)**: Prime Time Anchor, National Bulletin, Breaking News, Field Reporter, Editorial, Financial Markets, Sports Desk, Weather.
2. **Storytelling & Kahaniyaan (9–18)**: Classic Katha Vachak, Dadi Ki Kahani, Horror & Mystery, Romantic Fiction, Panchatantra Tales, Puranic Mythology, Sci-Fi Adventure, Detective Thriller, Historical Biographies, Serialized Audio Novels.
3. **YouTube & Social Media (19–28)**: Tech Reviewer, Lifestyle Vlogger, Viral Shorts & Reels, Amazing Facts Girl, Gaming Streamer, Motivation Quotes, Personal Finance Creator, DIY & Craft Guide, Movie Recap, Book Summary Host.
4. **Advertisements & Commercials (29–38)**: Luxury & Premium Brand, Beauty & Skincare, Mega Festive Sale, Family FMCG & Food, Automotive Power, Trendy Apparel, Health & Pharma, Banking & Loans, Quirky Radio Spot, Toys & Candy.
5. **Documentaries & History (39–46)**: Wildlife & Nature Explorer, Earth & Space Explainer, Ancient Dynasties, Art & Monument Heritage, Military Battles & Defense, Deep Sea Mysteries, True Crime Chronicles, Social Issues.
6. **Educational & E-Learning (47–56)**: Civil Services & UPSC Professor, Primary School Tutor, Physics & Engineering, Biology & NEET, History Lecturer, Hindi Sahitya & Kavita, Python & Coding, Spoken English, Exam Strategy, Moral Values.
7. **Corporate & Business (57–66)**: Executive Keynote & CEO, HR Onboarding & Compliance, Financial Results & Investor Call, Enterprise B2B Sales, IT & Digital Transformation, Product Launch Host, Industrial Safety & EHS, CSR Impact, Townhall & Podcast, Talent Acquisition.
8. **Podcasts & Conversations (67–74)**: Late Night Radio RJ, Cozy Coffee Chat, Deep-Dive Interviewer, Human Stories, Chai Pe Charcha Banter, Film Critic, Philosophy & Wisdom, Myth Buster.
9. **Meditation & Wellness (75–82)**: Guided Breathwork, Sleep Story & Insomnia, Morning Gratitude Affirmations, Satsang & Vedic Reflection, Chakra Balancing & Sound Healing, Zen Mindfulness, Forest Nature Walk, Temple Prayers.
10. **IVR, Telephony & Support (83–90)**: Bank IVR & Phone Banking, Telecom Network Assistant, Airline Booking & Airport, Delivery & Courier Bot, Hospital Appointment, Citizen Helpline, Hotel Concierge, Broadband Tech Support.
11. **Formal Announcements (91–95)**: Metro Train Announcer, Railway Station PA, Airport Gate Announcer, Civic Emergency Alert, Shopping Mall PA.
12. **Creative & Character Voices (96–100)**: 1950s Radio Sleuth, Fairy Tale Guide, Live Cricket Commentator, Shayari & Ghazal Reciter, Village Wisdom Elder.

---

## 4. Audio Caching System

- **Cache Key**: Deterministic SHA-256 hash computed from normalized text, voice profile ID, speed, pitch offset, output format, and engine settings.
- **Cache Hit Behavior**: Returns cached audio immediately via HTTP 200 without running model inference.
- **Storage**: Audio files stored under `backend/data/cache/<sha256_hash>.<ext>`.

---

## 5. Devanagari-Aware Text Chunking

Unlike naive sentence splitters that cut text indiscriminately or corrupt Hindi ligatures, the `split_hindi_text` utility:
- Splits along Hindi Purna Viram (`।` `\u0964`), Deergh Viram (`॥` `\u0965`), `.`, `!`, `?`.
- Respects clause boundaries (commas, semicolons, dashes) when long run-on sentences exceed `MAX_CHARS_PER_CHUNK`.
- Protects Devanagari virama/halant (`्`) and matras so word pronunciations remain unaltered.
- Merges audio chunks seamlessly.

---

## 6. API Reference

### 1. List All Voices
```http
GET /api/voices?include_presets=true&category=News%20%26%20Broadcast&gender=male
```

### 2. Audition Lazy-Loaded Preview Audio
```http
GET /api/voices/{voice_id}/preview
```
*Returns: `audio/wav` preview stream (instant cache hit on subsequent calls).*

### 3. Generate Speech
```http
POST /api/voices/{voice_id}/generate
Content-Type: application/json

{
  "text": "नमस्ते, हमारे पॉडकास्ट में आपका हार्दिक स्वागत है।",
  "speed": 1.0,
  "pitch": 0.0,
  "format": "wav"
}
```

*Response (201 Created):*
```json
{
  "id": "gen_abcdef123456",
  "voice_id": "hi-male-news-anchor-01",
  "voice_name": "Rohit — Prime Time News",
  "created_at": "2026-10-08T12:00:00Z",
  "text_preview": "नमस्ते, हमारे पॉडकास्ट में आपका हार्दिक स्वागत है।",
  "full_text_chars": 51,
  "audio_url": "/api/generations/gen_abcdef123456/audio",
  "duration_seconds": 3.82,
  "chunk_count": 1
}
```

---

## 7. Local Development Setup

### Backend:
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend:
```bash
cd frontend
npm install
npm run dev
```

### Run Automated Tests:
```bash
# Backend pytest suite (15 tests)
cd backend && .\.venv\Scripts\pytest

# Frontend vitest suite
cd frontend && npm test
```

---

## 8. Docker Deployment

### `Dockerfile`:
```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
