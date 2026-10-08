# 🎙️ Voice Clone App — Complete Technical Documentation

> **Project:** Shakir Voice Clone App  
> **Stack:** FastAPI (Python) + React (TypeScript) + MeloTTS + OpenVoice V2 + Microsoft Edge TTS  
> **Last Updated:** October 2026

---

## ⚡ Quick Start — App Kaise Chalayein

> Yeh commands daily use ke liye hain. Pehli baar setup ke liye neeche "First Time Setup" dekho.

### Roz Chalane ke Commands (Daily Use)

Do alag terminals kholo aur dono ek saath run karo:

**Terminal 1 — Backend (FastAPI Server)**
```bash
cd "d:\Coding destop folder\shakir-voice-clone-app\backend"

# Virtual environment activate karo
.venv\Scripts\activate

# Backend start karo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000


 .\.venv\Scripts\activate ; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```


> Backend ready hoga jab terminal mein `Application startup complete.` dikhe.  
> URL: **http://localhost:8000**  
> API Docs: **http://localhost:8000/docs**

---

**Terminal 2 — Frontend (React + Vite)**
```bash
cd "d:\Coding destop folder\shakir-voice-clone-app\frontend"

# Frontend dev server start karo
npm run dev
```
> URL: **http://localhost:5173**

---

### First Time Setup (Sirf Ek Baar)

**Step 1 — Backend setup:**
```bash
# Step 1: backend folder mein jao
cd "d:\Coding destop folder\shakir-voice-clone-app\backend"

# Step 2: .env banao (pehli baar sirf)
copy .env.example .env

# Step 3: venv activate karo (ZAROORI — pehle yeh karo)
.venv\Scripts\activate

# Step 4: ab install karo (venv activated hone ke baad)
pip install -r requirements.txt

# Step 5: server start karo
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

```

**Step 2 — Frontend setup:**
```bash
cd "d:\Coding destop folder\shakir-voice-clone-app\frontend"

# Node modules install karo
npm install
```

**Step 3 — OpenVoice V2 model checkpoints download karo:**
```bash
# backend/models/checkpoints_v2/ folder mein yeh files chahiye:
#   converter/config.json
#   converter/checkpoint.pth
#   base_speakers/ses/en-default.pth
# (README.md mein download link diya hai)
```

---

### Useful Extra Commands

| Command | Kya karta hai |
|---------|--------------|
| `uvicorn app.main:app --reload` | Backend with auto-reload (development) |
| `uvicorn app.main:app --host 0.0.0.0 --port 8000` | Network pe expose karo |
| `npm run dev` | Frontend dev server (port 5173) |
| `npm run build` | Frontend production build |
| `curl http://localhost:8000/api/model/status` | Model load status check karo |
| `curl http://localhost:8000/health` | Server health check |

---

## 📋 Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Directory Structure](#3-directory-structure)
4. [Currently Integrated Models](#4-currently-integrated-models)
5. [How Each Model is Used — Step by Step](#5-how-each-model-is-used--step-by-step)
6. [Core Services Explained](#6-core-services-explained)
7. [API Endpoints Reference](#7-api-endpoints-reference)
8. [Voice Types: Preset vs Custom Clone](#8-voice-types-preset-vs-custom-clone)
9. [Configuration Reference (.env)](#9-configuration-reference-env)
10. [How to Add a New TTS Model](#10-how-to-add-a-new-tts-model)
11. [Deterministic Cache System](#11-deterministic-cache-system)
12. [Hindi Chunking System](#12-hindi-chunking-system)
13. [Audio Pipeline](#13-audio-pipeline)
14. [Known Limitations & Future Ideas](#14-known-limitations--future-ideas)

---

## 1. Project Overview

Yeh ek **Personal Voice Clone TTS (Text-to-Speech) App** hai jisme aap:
1. Apni ya kisi bhi insaan ki awaaz ka **3-180 second ka recording** upload karte ho
2. System us recording se **voice ka "tone color embedding"** extract karta hai
3. Phir aap jo bhi text type karo — usse us extracted voice mein **speech generate** hoti hai
4. **100+ preset Hindi/English voices** bhi available hain bina kisi cloning ke

```
User Recording → Tone Color Embedding Extraction (OpenVoice V2)
                         ↓
Text Input → Base Audio (MeloTTS / Edge TTS) → Timbre Transfer → Output Audio
```

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                   │
│   Port: 5173                                                     │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Voice List │  │ Voice Create │  │   Generate Speech      │  │
│  │  & Presets  │  │ (Upload/Rec) │  │   (Text Input + Play)  │  │
│  └──────┬──────┘  └──────┬───────┘  └──────────┬─────────────┘  │
│         │                │                      │                │
└─────────┼────────────────┼──────────────────────┼────────────────┘
          │    HTTP REST API│                      │
          ▼                ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│   Port: 8000                                                     │
│                                                                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │ routes_voices  │  │routes_generation│  │ routes_health    │  │
│  │ /api/voices    │  │/api/voices/{id} │  │ /api/model/status│  │
│  │                │  │  /generate      │  │                  │  │
│  └───────┬────────┘  └────────┬────────┘  └──────────────────┘  │
│          │                   │                                   │
│  ┌───────▼────────────────────▼──────────────────────────────┐  │
│  │                    SERVICES LAYER                          │  │
│  │                                                            │  │
│  │  voice_profile_service  |  tts_service  |  cache_service  │  │
│  │  model_service          |  audio_service|  hindi_chunker  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼───────────────────────────────┐   │
│  │                    MODEL LAYER                            │   │
│  │                                                           │   │
│  │  ┌───────────────┐     ┌────────────────────────────┐    │   │
│  │  │  MeloTTS      │     │     OpenVoice V2            │    │   │
│  │  │ (English Base)│     │  ToneColorConverter +       │    │   │
│  │  │               │     │  SE Extractor               │    │   │
│  │  └───────────────┘     └────────────────────────────┘    │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │     Microsoft Edge TTS (Cloud - Free, No Key)      │  │   │
│  │  │     400+ Neural Voices incl. Hindi voices           │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  STORAGE (backend/data/)                  │    │
│  │  voices/ | generated/ | cache/ | temp/ | previews/       │    │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Directory Structure

```
shakir-voice-clone-app/
│
├── 📁 backend/                          # Python FastAPI server
│   ├── .env                             # Machine-specific config (gitignored)
│   ├── .env.example                     # Template for .env
│   ├── requirements.txt                 # Python dependencies
│   │
│   ├── 📁 app/                          # Main application package
│   │   ├── main.py                      # FastAPI app init + startup (model load)
│   │   ├── config.py                    # All Settings (reads from .env)
│   │   ├── hindi_voices.py              # 100 Hindi voice definitions (large file)
│   │   │
│   │   ├── 📁 api/                      # HTTP Route handlers
│   │   │   ├── routes_voices.py         # GET/POST/DELETE /api/voices
│   │   │   ├── routes_generations.py    # POST /api/voices/{id}/generate
│   │   │   └── routes_health.py         # GET /api/model/status
│   │   │
│   │   ├── 📁 services/                 # Business logic
│   │   │   ├── model_service.py         # Loads MeloTTS + OpenVoice V2 at startup
│   │   │   ├── tts_service.py           # Main text-to-speech orchestration
│   │   │   ├── voice_profile_service.py # Voice CRUD + embedding extraction
│   │   │   ├── audio_service.py         # ffmpeg audio conversion
│   │   │   ├── cache_service.py         # SHA-256 deterministic cache
│   │   │   ├── hindi_chunker.py         # Devanagari-aware text splitting
│   │   │   └── history_service.py       # Generation history log
│   │   │
│   │   ├── 📁 schemas/                  # Pydantic request/response models
│   │   └── 📁 utils/                    # IDs, file safety, logging
│   │
│   ├── 📁 models/                       # Local model checkpoints (gitignored)
│   │   └── checkpoints_v2/              # OpenVoice V2 weights
│   │       ├── converter/               # ToneColorConverter weights
│   │       │   ├── config.json
│   │       │   └── checkpoint.pth
│   │       └── base_speakers/ses/       # MeloTTS source embeddings
│   │           └── en-default.pth
│   │
│   └── 📁 data/                         # Runtime data (gitignored)
│       ├── voices/                      # Custom voice profiles
│       │   └── voice_abc123/
│       │       ├── reference.wav        # Cleaned recording
│       │       ├── se.pth               # Tone color embedding (PyTorch tensor)
│       │       └── metadata.json        # id, name, created_at, ready
│       ├── generated/                   # Generated audio files
│       ├── cache/                       # SHA-256 keyed audio cache
│       ├── temp/                        # Temporary chunks (auto-cleaned)
│       └── previews/                    # Cached voice preview clips
│
└── 📁 frontend/                         # React + TypeScript + Vite
    ├── package.json
    ├── vite.config.ts
    └── 📁 src/
        ├── App.tsx
        ├── styles.css
        ├── 📁 components/               # Reusable UI components
        ├── 📁 pages/                    # Page-level components
        ├── 📁 services/                 # API call functions
        ├── 📁 hooks/                    # Custom React hooks
        ├── 📁 types/                    # TypeScript type definitions
        └── 📁 data/                     # Static data (voice categories etc.)
```

---

## 4. Currently Integrated Models

### Model 1: Microsoft Edge TTS (`edge-tts`)

| Property | Detail |
|----------|--------|
| **Package** | `edge-tts` (Python) |
| **Type** | Cloud-based Neural TTS (Free, no API key) |
| **Used For** | All **preset voices** (Hindi + English) |
| **Hindi Voices** | `hi-IN-MadhurNeural`, `hi-IN-SwaraNeural`, + 100 more |
| **English Voices** | `en-IN-PrabhatNeural`, `en-US-JennyNeural`, etc. |
| **Latency** | ~1-3 seconds (network dependent) |
| **Quality** | High quality neural voices |
| **Pitch Control** | Yes (+-Hz) |
| **Speed Control** | Yes (+-% rate) |
| **Offline** | No — Requires internet |
| **Config Key** | `HINDI_TTS_ENGINE=edge` |

**Code location:** `backend/app/services/tts_service.py` → `_synthesize_edge_tts()`

```python
# Edge TTS aise call hota hai
comm = edge_tts.Communicate(text, "hi-IN-MadhurNeural", rate="+10%", pitch="+2Hz")
await comm.save("output.mp3")
```

---

### Model 2: MeloTTS (Local)

| Property | Detail |
|----------|--------|
| **Package** | `git+https://github.com/myshell-ai/MeloTTS.git` |
| **Type** | Local Neural TTS (runs on your machine) |
| **Used For** | **Custom cloned voices** — English text ka base audio generate karna |
| **Supported Languages** | EN, ES, FR, ZH, JP, KR (via `MELO_LANGUAGE` config) |
| **Default Speaker** | `EN-Default` (via `MELO_SPEAKER` config) |
| **Latency** | ~2-5 seconds CPU, ~0.5-1s GPU |
| **Quality** | Good for English |
| **Hindi Support** | Limited — falls back to Edge TTS for Devanagari |
| **Offline** | Yes — Fully offline once downloaded |
| **Config Key** | `MELO_LANGUAGE`, `MELO_SPEAKER` |

**Code location:** `backend/app/services/model_service.py`, `tts_service.py` line 186-195

```python
# MeloTTS aise use hota hai
from melo.api import TTS as MeloTTS
base_speaker_tts = MeloTTS(language="EN", device="cpu")
base_speaker_tts.tts_to_file(text, speaker_id, output_path, speed=1.0)
```

---

### Model 3: OpenVoice V2 — ToneColorConverter (Local)

| Property | Detail |
|----------|--------|
| **Package** | `git+https://github.com/myshell-ai/OpenVoice.git@main` |
| **Type** | Voice cloning — Tone Color Transfer |
| **Used For** | Custom voice cloning — base audio ki timbre change karna |
| **What it does** | Base audio (MeloTTS/EdgeTTS) ko target voice ki timbre mein convert karta hai |
| **Input** | Base WAV + Source Embedding + Target Embedding |
| **Output** | Cloned voice WAV |
| **Checkpoint** | `models/checkpoints_v2/converter/checkpoint.pth` |
| **Latency** | ~1-3 seconds per chunk (CPU) |
| **Offline** | Yes — Fully offline |
| **License** | MIT |

**Code location:** `backend/app/services/model_service.py` line 93-101

```python
# OpenVoice V2 ToneColorConverter aise use hota hai
from openvoice.api import ToneColorConverter
converter = ToneColorConverter("config.json", device="cpu")
converter.load_ckpt("checkpoint.pth")

# Voice clone karna
converter.convert(
    audio_src_path="base_audio.wav",
    src_se=source_embedding,   # MeloTTS ki apni awaaz
    tgt_se=target_embedding,   # User ki cloned awaaz
    output_path="cloned.wav"
)
```

---

### Model 4: OpenVoice V2 — SE Extractor (Local)

| Property | Detail |
|----------|--------|
| **Package** | `openvoice.se_extractor` (part of OpenVoice) |
| **Type** | Tone Color Embedding Extractor |
| **Used For** | User ki recording se **tone color embedding (SE)** extract karna |
| **Input** | Reference WAV (user ki awaaz, 3-180 sec) |
| **Output** | `se.pth` — PyTorch tensor (small file, KB range) |
| **When runs** | Only at **voice profile creation** time (one-time per profile) |
| **Storage** | `backend/data/voices/<voice_id>/se.pth` |

**Code location:** `backend/app/services/voice_profile_service.py` line 282-297

```python
# SE extraction
from openvoice import se_extractor
target_se, _ = se_extractor.get_se(
    reference_wav_path, 
    tone_color_converter, 
    vad=True  # Voice Activity Detection — silence remove karta hai
)
torch.save(target_se.cpu(), "se.pth")
```

---

### Model Summary Table

| Model | Type | Used When | Offline? |
|-------|------|-----------|----------|
| **Edge TTS** | Cloud Neural TTS | Preset voices (100+), Hindi base for cloning | No |
| **MeloTTS** | Local Neural TTS | English base audio for custom cloning | Yes |
| **OpenVoice V2 ToneColorConverter** | Tone Color Transfer | Custom voice timbre transfer | Yes |
| **OpenVoice V2 SE Extractor** | Embedding Extractor | Voice profile creation (one-time) | Yes |

---

## 5. How Each Model is Used — Step by Step

### Flow A: Preset Voice Generation (e.g. "Madhur - Hindi Male")

```
User types text
       |
tts_service.generate_speech(voice_id="preset_hi_madhur", text="...")
       |
[Cache Check] → SHA-256 key → cache hit? → return cached file instantly
       | (cache miss)
get_preset_voice("preset_hi_madhur") → returns voice config
       |
split_hindi_text(text, max_chars=350)  ← Hindi Chunker
       |
For each chunk:
  _synthesize_edge_tts("hi-IN-MadhurNeural", chunk, speed, pitch)
    → edge_tts.Communicate() → saves MP3
    → ffmpeg: MP3 → WAV (mono, 22050Hz)
       |
concat_wavs([chunk1.wav, chunk2.wav, ...]) → final.wav
       |
Store in cache → Return audio URL
```

### Flow B: Custom Clone Voice Generation

```
User types text
       |
tts_service.generate_speech(voice_id="voice_abc123", text="...")
       |
[Cache Check] → SHA-256 key → cache hit? → return cached file instantly
       | (cache miss)
model_service.require_ready()  ← MeloTTS + OpenVoice loaded?
       |
torch.load("data/voices/voice_abc123/se.pth") → target_se tensor
       |
has_hindi_script(text)?
  YES → base audio via Edge TTS ("hi-IN-MadhurNeural")
  NO  → base audio via MeloTTS (English) [fallback: Edge TTS en-IN-PrabhatNeural]
       |
For each chunk:
  → base audio generate
  → ToneColorConverter.convert(base_audio, src_se, target_se) → cloned chunk
       |
concat_wavs() → final.wav
       |
Store in cache → Return audio URL
```

### Flow C: Voice Profile Creation (Cloning Setup — One Time)

```
User uploads recording (WebM/WAV/MP3)
       |
routes_voices.create_voice() → saves to temp/
       |
audio_service.convert_to_reference_wav()
  → ffmpeg: any format → mono WAV, 22050Hz
  → duration check: 3s ≤ dur ≤ 180s
       |
voice_profile_service._extract_and_save_embedding()
  → model_service.require_ready()
  → se_extractor.get_se(reference.wav, converter, vad=True)
  → torch.save(se.pth)
       |
metadata.json saved → Profile ready!
```

---

## 6. Core Services Explained

### `model_service.py` — Model Loader

**Role:** MeloTTS aur OpenVoice V2 ko **ek baar** startup pe load karta hai. Thread-safe singleton pattern use karta hai.

**Key States:**
- `NOT_STARTED` → `LOADING` → `READY` / `ERROR`

**Important:** Agar model load fail ho toh bhi server start hota hai. Generation endpoints 503 return karte hain model load hone tak.

---

### `tts_service.py` — Main TTS Orchestrator

**Role:** Text ko speech mein convert karta hai. Preset aur custom voices dono handle karta hai. Cache check pehle karta hai, phir appropriate engine choose karta hai.

**Key Functions:**
- `generate_speech()` — Main entry point
- `_synthesize_edge_tts()` — Edge TTS wrapper
- `split_into_chunks()` — Text chunking alias

---

### `voice_profile_service.py` — Voice CRUD

**Role:** Voice profiles create/read/update/delete karta hai. Preset voices bhi yahan define hain.

**Key Data:**
- `PRESET_VOICES` — 6 hardcoded premium voices
- `HINDI_VOICES` — 100 voices from `hindi_voices.py`
- `ALL_PRESET_VOICES` — Combined dictionary (both merged)

---

### `audio_service.py` — Audio Processing

**Role:** `ffmpeg` use karke any audio format ko model-compatible WAV mein convert karta hai.

**Target Format:** Mono, 22050 Hz, 16-bit PCM WAV

---

### `cache_service.py` — Deterministic Cache

**Role:** Same text+voice+speed+pitch combo pe dubara model run nahi karta — cached file return karta hai instantly.

**Key:** `SHA-256(text + voice_id + speed + pitch + format)` → filename

---

### `hindi_chunker.py` — Text Splitter

**Role:** Lamba text ko natural boundaries pe split karta hai taaki model quality degrade na ho.

**Priority:** `।` `॥` `.` `!` `?` `\n\n` → phir `,` `;` `:` `-` → phir whitespace

---

## 7. API Endpoints Reference

### Voices

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/voices` | Sab voices list karo (presets + custom) |
| `GET` | `/api/voices?include_presets=false` | Sirf custom voices |
| `GET` | `/api/voices?category=News` | Category filter |
| `GET` | `/api/voices?gender=male` | Gender filter |
| `POST` | `/api/voices` | Naya voice profile banao (multipart: name + file) |
| `GET` | `/api/voices/{voice_id}` | Ek voice ki detail |
| `PATCH` | `/api/voices/{voice_id}` | Voice rename karo |
| `DELETE` | `/api/voices/{voice_id}` | Voice delete karo |
| `POST` | `/api/voices/{voice_id}/recompute` | SE embedding dobara extract karo |
| `GET` | `/api/voices/{voice_id}/reference-audio` | Original recording download |
| `GET` | `/api/voices/{voice_id}/preview` | Short preview audio |

### Generations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/voices/{voice_id}/generate` | Speech generate karo |
| `GET` | `/api/generations` | Sab generations ki history |
| `GET` | `/api/generations/{gen_id}` | Ek generation ki detail |
| `GET` | `/api/generations/{gen_id}/audio` | Audio file download |
| `DELETE` | `/api/generations/{gen_id}` | Generation delete karo |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/model/status` | Model load status check |
| `GET` | `/health` | Server health check |

### Generate Request Body Example

```json
{
  "text": "नमस्ते, यह एक test है।",
  "speed": 1.0,
  "pitch": 0.0,
  "format": "wav"
}
```

---

## 8. Voice Types: Preset vs Custom Clone

### Preset Voices (Ready to Use — No Model Needed)

**6 Built-in Premium Voices** hardcoded in `voice_profile_service.py`:

| ID | Name | Gender | Engine |
|----|------|--------|--------|
| `preset_hi_madhur` | Madhur (Hindi Male) | Male | Edge TTS |
| `preset_hi_swara` | Swara (Hindi Female) | Female | Edge TTS |
| `preset_en_in_prabhat` | Prabhat (Indian English Male) | Male | Edge TTS |
| `preset_en_in_neerja` | Neerja (Indian English Female) | Female | Edge TTS |
| `preset_en_us_jenny` | Jenny (US English Female) | Female | Edge TTS |
| `preset_en_us_guy` | Guy (US English Male) | Male | Edge TTS |

**100 Additional Hindi Voices** from `hindi_voices.py`:
- Categories: News & Broadcast, Educational, Storytelling, Devotional, Corporate, Conversational, etc.
- Both Male & Female genders
- Various styles: Authoritative, Calm, Energetic, Formal, etc.

### Custom Cloned Voices (Requires Model Checkpoints)

- User apni recording (3-180s) upload karta hai
- OpenVoice V2 tone color extract karta hai → `se.pth` save hoti hai
- Generation mein: MeloTTS (English) ya Edge TTS (Hindi) → OpenVoice V2 timbre transfer
- Requires `models/checkpoints_v2/` downloaded hona

---

## 9. Configuration Reference (.env)

File location: `backend/.env` (copy from `backend/.env.example`)

```bash
# ---- Server ----------------------------------------
HOST=127.0.0.1
PORT=8000
CORS_ORIGINS=http://localhost:5173

# ---- Storage ----------------------------------------
DATA_DIR=./data                     # Sab data yahan store hoga

# ---- Model Config -----------------------------------
DEVICE=auto                         # auto | cpu | cuda:0
OPENVOICE_CHECKPOINT_DIR=./models/checkpoints_v2  # OpenVoice V2 weights path
MELO_LANGUAGE=EN                    # EN | ES | FR | ZH | JP | KR
MELO_SPEAKER=EN-Default             # MeloTTS speaker ID
ENABLE_WATERMARK=false              # Audio watermark on/off

# ---- Text Limits ------------------------------------
MAX_CHARS_PER_CHUNK=350             # Ek chunk max characters
MAX_TOTAL_CHARS=5000                # Input text max characters

# ---- Upload Limits ----------------------------------
MAX_UPLOAD_MB=25                    # Max upload file size
MIN_REFERENCE_SECONDS=3             # Min recording length (seconds)
MAX_REFERENCE_SECONDS=180           # Max recording length (seconds)
```

---

## 10. How to Add a New TTS Model

Agar aap koi naya TTS model integrate karna chahte ho (jaise **Coqui XTTS v2**, **Bark**, **Parler TTS**, **F5-TTS**, **Piper TTS**), toh yeh exact 9 steps follow karo:

---

### Step 1: `requirements.txt` mein dependency add karo

```bash
# backend/requirements.txt mein add karo
your-new-tts-library==x.x.x

# Example for XTTS v2:
# TTS==0.22.0
```

---

### Step 2: `config.py` mein config keys add karo

```python
# backend/app/config.py → Settings class mein add karo:

class Settings:
    # ... existing fields ...
    
    # --- New Model ---
    NEW_MODEL_CHECKPOINT: Path = Path(
        os.getenv("NEW_MODEL_CHECKPOINT", str(BACKEND_DIR / "models" / "new_model"))
    ).resolve()
    NEW_MODEL_LANGUAGE: str = os.getenv("NEW_MODEL_LANGUAGE", "hi")
```

---

### Step 3: `.env.example` update karo

```bash
# backend/.env.example mein add karo:

# New Model
NEW_MODEL_CHECKPOINT=./models/new_model
NEW_MODEL_LANGUAGE=hi
```

---

### Step 4: `model_service.py` mein model load karo

```python
# backend/app/services/model_service.py

class ModelService:
    def __init__(self) -> None:
        # ... existing fields ...
        self.new_model_tts = None  # <-- naya field add karo

    def load(self) -> None:
        # ... existing loading code ...
        
        # Naye model ka loading block — end mein add karo
        try:
            from your_tts_library import YourTTSModel
            new_model_path = settings.NEW_MODEL_CHECKPOINT
            if new_model_path.exists():
                self.new_model_tts = YourTTSModel.from_pretrained(str(new_model_path))
                logger.info("New model loaded successfully on device=%s", self.device)
            else:
                logger.warning(
                    "New model checkpoint not found at %s, skipping.", new_model_path
                )
        except Exception as e:
            logger.warning("New model failed to load: %s", e)
            # NOTE: Isko main status block mein mat dalo
            # Optional model hai, main stack ka READY status change nahi hona chahiye
```

---

### Step 5: `tts_service.py` mein synthesis function add karo

```python
# backend/app/services/tts_service.py mein naya function add karo:

def _synthesize_new_model(
    text: str, 
    speed: float, 
    out_wav_path: Path,
    language: str = "hi"
) -> float:
    """
    New TTS model se audio generate karo.
    Returns: duration in seconds
    """
    if model_service.new_model_tts is None:
        raise RuntimeError(
            "New model is not loaded. Check /api/model/status for details."
        )
    
    # Apni model ka inference code yahan:
    model_service.new_model_tts.synthesize(
        text=text,
        output_path=str(out_wav_path),
        speed=speed,
        language=language
    )
    
    return get_duration_seconds(out_wav_path)
```

---

### Step 6: `generate_speech()` mein logic add karo

```python
# backend/app/services/tts_service.py → generate_speech() function mein
# Yeh section: preset voice block ke BAAD, clone voice block se PEHLE add karo

    # --- New Model Preset Voices ---
    if voice_id.startswith("new_model_"):
        chunks = split_hindi_text(text, settings.MAX_CHARS_PER_CHUNK)
        temp_dir = settings.TEMP_DIR
        temp_dir.mkdir(parents=True, exist_ok=True)
        chunk_paths: list[Path] = []
        req_id = out_path.stem
        
        try:
            for i, chunk in enumerate(chunks):
                chunk_file = temp_dir / f"new_{req_id}_{i}.wav"
                _synthesize_new_model(chunk, speed, chunk_file)
                chunk_paths.append(chunk_file)
            
            if len(chunk_paths) == 1:
                shutil.copyfile(chunk_paths[0], out_path)
            else:
                concat_wavs(chunk_paths, out_path)
            
            duration = get_duration_seconds(out_path)
            store_cached_audio(out_path, text, voice_id, speed, pitch, format)
            return duration, len(chunks)
        finally:
            for cp in chunk_paths:
                cp.unlink(missing_ok=True)
```

---

### Step 7: `voice_profile_service.py` mein preset add karo (Optional)

```python
# backend/app/services/voice_profile_service.py → PRESET_VOICES dict mein:

PRESET_VOICES: dict[str, dict] = {
    # ... existing presets ...
    
    "new_model_hindi_male": {
        "id": "new_model_hindi_male",
        "name": "Arjun (Hindi Male - New Model)",
        "created_at": "2026-01-01T00:00:00Z",
        "ready": True,
        "duration_seconds": None,
        "is_preset": True,
        "gender": "male",
        "category": "General",
        "style": "Natural",
        "description": "Natural Hindi male voice powered by New Model.",
        "engine": "new_model",        # engine naam — lowercase
        "base_speaker": "hindi_male",
        "voice": "hindi_male",
        "preview_text": "नमस्ते, मैं नया TTS मॉडल हूँ।",
    },
}
```

---

### Step 8: `HINDI_TTS_ENGINE` config update karo (Optional)

```python
# backend/app/config.py mein comment update karo:
# Preferred Hindi TTS Engine: "auto" | "indic-parler" | "piper" | "edge" | "new_model"
HINDI_TTS_ENGINE: str = os.getenv("HINDI_TTS_ENGINE", "auto")
```

---

### Step 9: Test karo

```bash
# 1. Backend restart karo
cd backend
uvicorn app.main:app --reload

# 2. Model status check karo
curl http://localhost:8000/api/model/status

# 3. Naye preset voice se generate karo
curl -X POST http://localhost:8000/api/voices/new_model_hindi_male/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "नमस्ते यह test है", "speed": 1.0}'
```

---

### New Model Integration Checklist

```
[ ] requirements.txt → dependency add kiya
[ ] config.py → Settings class mein env vars add kiye
[ ] .env.example → naye vars ka documentation add kiya
[ ] model_service.py → ModelService.__init__() mein field add kiya
[ ] model_service.py → load() mein loading block add kiya
[ ] tts_service.py → synthesis function likhdi
[ ] tts_service.py → generate_speech() mein routing logic add kiya
[ ] voice_profile_service.py → PRESET_VOICES mein entry add ki (optional)
[ ] Backend restart + /api/model/status check kiya
[ ] Test generation kiya
```

---

## 11. Deterministic Cache System

Cache system ensures ki **same request dobara model nahi chalata.**

**Cache Key Formula:**
```python
key = SHA-256({
    "text": normalized_text,    # whitespace normalize hota hai
    "voice_id": voice_id,
    "speed": round(speed, 3),
    "pitch": round(pitch, 2),
    "format": format            # "wav"
})
```

**Storage Path:** `backend/data/cache/<sha256_key>.wav`

**Cache Hit Condition:** File exists AND size > 512 bytes

**Cache Miss:** Model run karta hai, result cache mein store hota hai

**Cache Clear Karna:** Manually `backend/data/cache/` ke saare files delete karo

---

## 12. Hindi Chunking System

Long text (350+ chars) models ke liye problematic hoti hai — quality degrade hoti hai. Chunker text ko natural phonetic boundaries pe split karta hai.

**Split Priority (highest to lowest):**

| Priority | Boundary | Unicode |
|----------|---------|---------|
| 1 (highest) | Hindi Purna Viram (।) | `\u0964` |
| 2 | Deergh Viram (॥) | `\u0965` |
| 3 | Western sentence enders (. ! ?) | ASCII |
| 4 | Paragraph breaks | `\n\n` |
| 5 | Comma, semicolon, colon, dash (,  ;  :  -  –  —) | Mixed |
| 6 (lowest) | Whitespace (word boundary) | ASCII |

**Default max chunk size:** 350 chars (configurable via `MAX_CHARS_PER_CHUNK`)

**Never splits:** Mid-word ya Devanagari conjuncts ke beech mein

---

## 13. Audio Pipeline

```
User Upload (any format: webm, mp3, wav, ogg, m4a, aac)
       |
ffmpeg: any → mono WAV, 22050 Hz, 16-bit PCM
       |
Duration Validation: 3s <= duration <= 180s
       |
Saved as: data/voices/<voice_id>/reference.wav
       |
OpenVoice SE Extractor → se.pth (PyTorch tensor, small file)

===== GENERATION TIME =====

Text Input → Hindi Chunker → [chunk1, chunk2, chunk3, ...]
       |
Per chunk:
  Option A (Hindi/Devanagari text):
    → Edge TTS MP3 → ffmpeg → WAV
  Option B (English text + Custom Clone):
    → MeloTTS → WAV directly
    (fallback: Edge TTS en-IN-PrabhatNeural)
       |
  (Custom clone only):
    → OpenVoice ToneColorConverter.convert() → cloned chunk WAV
       |
All chunks → concat_wavs() → Final output WAV
       |
Store in SHA-256 cache → Serve via /api/generations/{id}/audio
```

---

## 14. Known Limitations & Future Ideas

### Current Limitations

| Issue | Reason | Workaround |
|-------|--------|------------|
| Hindi voice cloning quality medium | MeloTTS Hindi support weak; uses Edge TTS as base | Use high-quality clear recording |
| Preset voices require internet | Edge TTS is cloud-based | Use Piper TTS for offline (future) |
| MeloTTS only English well | Training data limited to English | Use for English-only cloning |
| Max 5000 chars per request | Model quality degrades on very long text | Split into multiple requests |
| CPU inference slow | GPU not used by default | Set `DEVICE=cuda:0` in .env if GPU available |

### Future Model Integration Ideas

| Model | Purpose | Key Benefit |
|-------|---------|-------------|
| **XTTS v2** (Coqui) | Better multilingual cloning | Hindi + English both handled well |
| **Bark** (Suno AI) | Emotional/expressive TTS | Natural prosody, sound effects |
| **Parler TTS** | Description-guided voices | Control style via text prompt |
| **Indic Parler TTS** | India-specific neural TTS | Better Indian language support |
| **F5-TTS** | Zero-shot voice cloning | Faster, no fine-tuning needed |
| **Piper TTS** | Fast offline Hindi TTS | No internet dependency for presets |
| **StyleTTS 2** | High-quality style transfer | Better voice quality overall |

### Performance Tips

1. **GPU use karo:** `DEVICE=cuda:0` set karo `.env` mein — 5-10x speedup
2. **Cache ko leverage karo:** Same text dobara generate karo — instant response
3. **Chunk size tune karo:** `MAX_CHARS_PER_CHUNK=200` — better quality per chunk

---

## Quick Reference Card

```
Add a new TTS model?
  → model_service.py (load) + tts_service.py (synthesis) + config.py (env vars)

Add a new preset voice?
  → voice_profile_service.py → PRESET_VOICES dict

Modify existing Hindi voices?
  → backend/app/hindi_voices.py (100 voices yahan hain)

Change API behavior?
  → backend/app/api/routes_*.py

Clear audio cache?
  → backend/data/cache/ folder empty karo

Model checkpoints location?
  → backend/models/checkpoints_v2/

Frontend API call functions?
  → frontend/src/services/
```

---

*Documentation maintained by: Shakir | Project: shakir-voice-clone-app*
