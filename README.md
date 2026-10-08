# My Voice Studio — Professional Hindi AI Voice Platform & Voice Cloning

A full-stack, local AI voice platform featuring **100 selectable professional Hindi voice profiles** across 12 content categories (News, Storytelling, Ads, YouTube/Reels, Documentaries, Podcasts, Meditation, E-learning, IVR), plus personal voice cloning using OpenVoice V2.

> 📘 **Full Architecture & Model Research:** See [`HINDI_VOICE_STUDIO_ARCHITECTURE.md`](./HINDI_VOICE_STUDIO_ARCHITECTURE.md) for complete evaluation of AI4Bharat Indic Parler-TTS, Piper TTS, IndicF5, audio caching, and API specifications.

## 1. What it does

- **100 Professional Hindi Voice Profiles**: Select from 100 distinct Hindi voice personas configured with natural prosody, pitch, speaking rate, and domain styles.
- **Audition Previews**: Lazy-loaded, instantaneous audio preview for all 100 voices with persistent caching.
- **Deterministic Audio Caching**: Fast SHA-256 caching ensures repeated texts and settings return instantly without re-running models.
- **Devanagari-Aware Chunking**: Intelligently splits Hindi text along Purna Viram (`।`), Deergh Viram (`॥`), and punctuation boundaries.
- **Custom Voice Cloning**: Record or upload your voice once, extract tone color embedding, and generate speech in your personal timbre.

## 2. Features

- **Dashboard** — pick a voice, type text, generate, play, download, see recent history.
- **Voice Profiles** — record/upload, preview, re-record, save, rename, delete,
  recompute (rebuild the voice data from the saved recording without re-recording).
- **Text-to-Speech** — multi-line input, character count, long-text chunking at
  sentence boundaries (never mid-word), clear validation errors.
- **History** — every generation's text preview, voice used, timestamp, duration,
  and a link to its audio file.
- **Settings** — model status, storage locations, privacy notes.

## 3. Architecture

```
Browser (React + TS)
   |  fetch /api/*
   v
FastAPI backend (Python)
   |
   +-- voice_profile_service  -- creates/reads/renames/deletes voice profiles
   +-- audio_service          -- ffmpeg preprocessing (any format -> clean WAV)
   +-- model_service          -- loads MeloTTS + OpenVoice V2 once at startup
   +-- tts_service             -- text -> chunks -> MeloTTS -> OpenVoice conversion
   +-- history_service        -- generation history (JSON file)
   |
   v
Local filesystem: backend/data/{voices,generated,temp}, history.json
```

Generation flow: text → chunk (if long) → MeloTTS renders each chunk in a
generic voice → OpenVoice's `ToneColorConverter` re-colors each chunk to your
saved voice's timbre → chunks are concatenated → saved as a WAV → served to
the browser.

## 4. Model decision

**Selected model: OpenVoice V2** (https://github.com/myshell-ai/OpenVoice),
paired with **MeloTTS** (https://github.com/myshell-ai/MeloTTS) as the base
speech engine that OpenVoice re-colors.

| Item | Value |
|---|---|
| Model | OpenVoice V2 (+ MeloTTS as base speaker TTS) |
| Repository | github.com/myshell-ai/OpenVoice, github.com/myshell-ai/MeloTTS |
| Code license | MIT (both projects) |
| Model-weight license | MIT — OpenVoice states V1 and V2 checkpoints are free for commercial and personal use as of April 2024 |
| Personal use | Yes |
| Commercial use | Yes (per upstream license — verify on the repo before relying on this for anything beyond personal use, since licenses can change) |
| Attribution | Not required by MIT, but cite the project if you publish something built on it |
| Languages | English, Spanish, French, Chinese, Japanese, Korean natively (MeloTTS) |
| Reusable speaker data | Yes — a small "tone color embedding" (`se.pth`), see section 7 |
| Windows compatible | Yes (pure Python + PyTorch, no OS-specific code) |
| Hardware | Works on CPU; much faster with an NVIDIA GPU (CUDA) |

Why this over alternatives: OpenVoice V2 is one of the few actively
maintained, MIT-licensed, local voice-cloning projects with a genuine reusable
speaker embedding (not "record every time"), reasonable CPU performance, and
straightforward Windows installation via pip/conda — no Docker or paid API
required. **Verify the license and repo state yourself before you rely on
this** (see README "Model setup" for how); license terms of open-source
projects do change.

## 5. Hardware requirements

- **CPU only:** works, but a generation of ~1 sentence can take several
  seconds to ~1 minute depending on your CPU. 8GB+ RAM recommended.
- **NVIDIA GPU (optional):** if you have one and install the CUDA build of
  PyTorch, generation is roughly 10-50x faster. ~4GB+ VRAM is enough for this
  model. You do **not** need a GPU to use this app.
- No internet is required at runtime once models are installed (see "Offline
  usage" below) — internet is only used to install packages and download
  model weights once.

## 6. Folder structure

```
voice-clone-app/
  backend/
    app/
      main.py                FastAPI app + startup model loading
      config.py               all settings (env-driven)
      api/                    routes_health.py, routes_voices.py, routes_generations.py
      schemas/                pydantic request/response models
      services/                tts_service, voice_profile_service, audio_service,
                                history_service, model_service
      utils/                  ids.py, files.py (path-safety), logging.py
    data/                    voices/, generated/, temp/ (created automatically)
    tests/                   pytest suite (mocks the model, so it runs without GPU/weights)
    requirements.txt
    .env.example
    models/checkpoints_v2/   <- YOU put OpenVoice's downloaded checkpoints here
  frontend/
    src/
      components/            VoiceRecorder, AudioPlayer, GenerationHistory, ...
      pages/                  Dashboard, VoiceProfiles, History, Settings
      services/               api.ts, voiceApi.ts, generationApi.ts
      hooks/                  useVoices, useGeneration, useBackendHealth
      types/
    package.json
  CONFIGURATION.md
  CUSTOMIZATION.md
  README.md (this file)
```

## 7. Voice profile — what's actually stored

See the detailed doc-comment at the top of
`backend/app/services/voice_profile_service.py` — the short version:

- What's extracted: a **tone color embedding** ("SE" tensor) from your
  reference recording, via OpenVoice's `ToneColorConverter.extract_se()`.
- What's stored, per profile, in `backend/data/voices/<voice_id>/`:
  `reference.wav` (your cleaned recording), `se.pth` (the embedding),
  `metadata.json` (name, date, ready flag).
- **It survives restart** — it's a plain file, reloaded fresh each generation.
- If `se.pth` is deleted or a model upgrade needs a fresh embedding, use
  **Recompute** in the UI to rebuild it from `reference.wav` — no re-recording.
- Generation does **not** need `reference.wav` every time, only `se.pth`.
  `reference.wav` is kept only so the embedding can be recreated later.

## 8. Installation (Windows 10/11, from zero)

All commands are PowerShell, run from wherever you note as "project root".

### 8.1 Install prerequisites

**WHERE:** anywhere
**Python 3.10 or 3.11** (3.12 also generally works, but OpenVoice's
dependency chain is best-tested on 3.10/3.11):
```powershell
winget install Python.Python.3.11
python --version
```
Expected: `Python 3.11.x`

**Node.js 18+:**
```powershell
winget install OpenJS.NodeJS.LTS
node --version
```
Expected: `v20.x.x` (or similar)

**FFmpeg** (required for audio preprocessing):
```powershell
winget install Gyan.FFmpeg
ffmpeg -version
```
Expected: version banner, no "not recognized" error. If PowerShell doesn't
see it immediately, open a new PowerShell window (PATH changes need a fresh shell).

**Git** (to fetch OpenVoice's source):
```powershell
winget install Git.Git
git --version
```

### 8.2 Get the project and create a virtual environment

**WHERE:** PowerShell, wherever you keep projects
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
```
Expected: prompt now starts with `(.venv)`.
If you get an execution-policy error, run PowerShell as Administrator once:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

### 8.3 Install backend dependencies

**WHERE:** PowerShell, `backend/`, with `.venv` active
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```
This installs FastAPI, PyTorch (CPU build by default on Windows via pip),
OpenVoice (from GitHub), MeloTTS, and audio libraries. This step downloads
several hundred MB and can take 5-15 minutes.
If it fails on `wavmark` or `unidic-lite`, re-run the same command — these
occasionally need a retry due to secondary package downloads.

### 8.4 (Optional) NVIDIA GPU / CUDA path

Check first:
```powershell
nvidia-smi
```
If that prints a GPU table, you have an NVIDIA GPU. Then install the CUDA
build of PyTorch **instead of** the CPU build pip installed above:
```powershell
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
python -c "import torch; print(torch.cuda.is_available())"
```
Expected: `True`. If `nvidia-smi` fails or you don't have an NVIDIA GPU, skip
this section entirely — CPU works fine, just slower.

### 8.5 Download the model weights

**WHERE:** PowerShell, `backend/`
```powershell
python -m melo.download_utils  # downloads MeloTTS English checkpoint on first run automatically; this line is just a sanity check, MeloTTS also auto-downloads on first use
```
For OpenVoice V2's converter checkpoints:
1. Go to https://huggingface.co/myshell-ai/OpenVoiceV2 (or the download link
   on https://github.com/myshell-ai/OpenVoice) and download `checkpoints_v2.zip`.
2. Extract it so you end up with `backend/models/checkpoints_v2/converter/` and
   `backend/models/checkpoints_v2/base_speakers/`.

**This step needs internet.** After this, and after MeloTTS's own one-time
model download on first run, no further internet access is required to
generate speech.

### 8.6 Configure environment

**WHERE:** `backend/`
```powershell
Copy-Item .env.example .env
```
Edit `.env` only if your checkpoints ended up somewhere other than
`backend/models/checkpoints_v2` — see `CONFIGURATION.md`.

### 8.7 Test the model directly (optional but recommended)

**WHERE:** PowerShell, `backend/`, `.venv` active
```powershell
python -c "from app.services.model_service import model_service; model_service.load(); print(model_service.status, model_service.detail)"
```
Expected: `ModelStatus.READY None`. If you see `ModelStatus.ERROR ...`, the
message tells you exactly what's missing (usually a checkpoint path issue).

### 8.8 Start the backend

**WHERE:** PowerShell, `backend/`, `.venv` active
```powershell
uvicorn app.main:app --reload --port 8000
```
Expected: `Uvicorn running on http://127.0.0.1:8000`. Leave this window open.

### 8.9 Install and start the frontend

**WHERE:** a **new** PowerShell window, `frontend/`
```powershell
npm install
npm run dev
```
Expected: `Local: http://localhost:5173/`

### 8.10 Open the browser

Go to `http://localhost:5173`. The status dot near the top should turn
green ("Model ready") once the backend finishes loading (can take 10-60s the
first time).

### 8.11–8.16 First use

See "First-use instructions" below — the same 14 steps also work as your
installation smoke test (create profile → generate → restart → generate again
without recording).

## 9. Configuration

See **CONFIGURATION.md** for the full table of what you may/must/should not change.

## 10. Storage locations

- Voice profiles: `backend/data/voices/<voice-id>/`
- Generated audio: `backend/data/generated/<generation-id>.wav`
- History: `backend/data/history.json`
- Model checkpoints (you download these): `backend/models/checkpoints_v2/`

## 11. Backup / restore

Your voice profile is the thing that matters most here.

- **Back up:** copy the entire `backend/data/voices/<voice-id>/` folder
  somewhere safe (external drive, cloud folder you control).
- **Restore:** copy that folder back into `backend/data/voices/` before
  starting the backend. It will show up in the Voice Profiles list
  immediately (metadata is read from disk on every list request).
- **Portability:** the `se.pth` embedding is tied to this OpenVoice model
  version. It is **not guaranteed** to work if you switch to a different
  voice-cloning model later — but `reference.wav` is a plain WAV file, and can
  always be re-processed into a fresh embedding (with Recompute, or with any
  future model) without needing to re-record your voice.

## 12. Offline usage

After the one-time steps that need internet (`pip install`, downloading
OpenVoice checkpoints, MeloTTS's first-run auto-download), generation itself
makes **no network calls**. You can verify this yourself by disconnecting
from the internet after the first successful generation and generating again
— it will work. The frontend dev server and backend both run on
`localhost` regardless of connectivity.

## 13. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| "Model error" on Settings page | Checkpoint path wrong or files missing | Re-check `OPENVOICE_CHECKPOINT_DIR` in `.env` and that `converter/config.json` + `converter/checkpoint.pth` exist there |
| `ffmpeg` not found | Not installed / not on PATH | Reinstall ffmpeg, open a new terminal |
| Backend won't start: port in use | Something else is on 8000 | `uvicorn app.main:app --port 8001` and update `CORS_ORIGINS`/frontend proxy |
| CORS error in browser console | Frontend origin not in `CORS_ORIGINS` | Add it to `backend/.env` |
| Microphone permission denied | Browser blocked mic access | Click the lock icon in the address bar → allow microphone, reload |
| "Unsupported audio type" on upload | File isn't a common audio container | Convert to WAV/MP3 first, or record in-browser instead |
| Voice profile shows "needs recompute" | `se.pth` missing/corrupted | Click **Recompute** on that profile's card |
| Generation is very slow | Running on CPU | Expected — see "Hardware requirements"; a GPU install (8.4) helps a lot |
| `CUDA mismatch` / `out of memory` errors | GPU driver/CUDA version mismatch, or VRAM too small | Reinstall the matching PyTorch CUDA build (8.4), or fall back to CPU by setting `DEVICE=cpu` in `.env` |
| `pip install -r requirements.txt` fails on `torch` | No matching wheel for your Python version | Use Python 3.10 or 3.11 (see 8.1) |

## 14. Privacy

No analytics. No tracking. No third-party voice upload. Your recordings and
generated audio never leave your machine at runtime. Network access happens
only during installation (`pip`/`npm install`) and the one-time model
checkpoint download.

## 15. License information

- This project's own code: use it however you like for personal purposes.
- OpenVoice V2 and MeloTTS: MIT License (see section 4 above) — verify current
  terms at the repos linked there before any commercial use.
- Nothing here depends on a paid API.

## 16. Development commands

Backend:
```powershell
cd backend
.venv\Scripts\Activate.ps1
pytest                       # run backend tests (no GPU/model weights needed)
uvicorn app.main:app --reload
```
Frontend:
```powershell
cd frontend
npm run dev                  # dev server, http://localhost:5173
npm run build                # production build -> frontend/dist
npx tsc -b                   # typecheck only
```

## 17. First-use instructions

1. Start the backend (`uvicorn app.main:app --reload`, in `backend/`).
2. Start the frontend (`npm run dev`, in `frontend/`).
3. Open `http://localhost:5173`.
4. Check the status dot turns green ("Model ready").
5. Go to **Voice Profiles**, click **Start recording**, say a few sentences
   (10-30s of clear speech works well), click **Stop**.
6. Name it, e.g. "My Voice", click **Save profile**.
7. Go to **Dashboard**, select "My Voice" from the dropdown.
8. Type a test sentence.
9. Click **Generate speech**.
10. Click Play on the result.
11. Click **Download** to save the WAV.
12. Stop the backend (Ctrl+C) and start it again.
13. Refresh the frontend — "My Voice" is still in the dropdown (confirms persistence).
14. Generate again without touching the microphone — confirms you never have
    to record twice.

## 18. Honest limitations (read this)

- This was built and syntax/logic-tested (backend pytest suite, frontend
  TypeScript build) in an environment **without a GPU and without the actual
  OpenVoice/MeloTTS model weights installed** — those are multi-hundred-MB to
  multi-GB downloads that only make sense to fetch once, on your machine,
  where you'll actually run the app. The backend tests mock only the
  model-inference step; every other piece (API routes, file handling,
  validation, chunking logic, the whole frontend) has been run for real.
- Before you fully trust "MIT license, free for commercial use" for anything
  beyond personal use, check the current text at
  https://github.com/myshell-ai/OpenVoice yourself — license terms of
  external projects can change after this was written.
- CPU generation speed varies a lot by machine; if it feels too slow, the GPU
  path in 8.4 is the fix, not a code change.
