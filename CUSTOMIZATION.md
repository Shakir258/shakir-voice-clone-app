# Customization

For each item: file, exact spot, before → after, and whether a restart is needed.

## Application name / UI title

- **File:** `frontend/index.html`
- **Spot:** `<title>My Voice Studio</title>`
- **Before → After:** change the text between the tags.
- **Restart:** refresh the browser tab (no server restart needed).

- **File:** `frontend/src/App.tsx`
- **Spot:** `<div className="app-nav-brand">My Voice Studio</div>`
- **Restart:** Vite hot-reloads this automatically in dev.

## Logo / icon (favicon)

- **File:** add `frontend/public/favicon.ico`, then reference it in
  `frontend/index.html`: add `<link rel="icon" href="/favicon.ico" />` inside `<head>`.
- **Restart:** refresh the browser.

## Default voice profile name (placeholder text)

- **File:** `frontend/src/pages/VoiceProfiles.tsx`
- **Spot:** `placeholder='Name this voice, e.g. "My Voice"'`
- **Before → After:** change the placeholder string.
- **Restart:** none (dev hot-reload); rebuild for production.

## Default language

- **File:** `backend/.env`
- **Spot:** `MELO_LANGUAGE=EN`
- **Before → After:** `MELO_LANGUAGE=ES` (or FR/ZH/JP/KR) and set a matching
  `MELO_SPEAKER` for that language (see MeloTTS's docs for valid speaker IDs).
- **Restart:** backend (`uvicorn`).

## Default output format

Output is always 16-bit PCM WAV (see `audio_service.py`,
`TARGET_SAMPLE_RATE`). To change the sample rate:
- **File:** `backend/app/services/audio_service.py`
- **Spot:** `TARGET_SAMPLE_RATE = 22050`
- **Before → After:** e.g. `44100` — note the model itself was trained at a
  specific rate; changing this only affects *reference* audio preprocessing,
  not generated output, which follows the model's own config.
- **Restart:** backend.

## Default output folder

- **File:** `backend/.env`
- **Spot:** `DATA_DIR` is not in `.env.example` by default (defaults to
  `backend/data`) — add the line yourself: `DATA_DIR=D:/voice-app-data`
- **Restart:** backend.

## Maximum text length

- **File:** `backend/.env`
- **Spot:** `MAX_TOTAL_CHARS=5000`
- **Restart:** backend. (The frontend's `MAX_CHARS` constant in
  `frontend/src/pages/Dashboard.tsx` should be updated to match, or the UI
  will allow typing text the backend then rejects.)

## Theme (colors)

- **File:** `frontend/src/styles.css`
- **Spot:** the `:root { ... }` block at the top (`--bg`, `--panel`,
  `--accent`, etc.)
- **Before → After:** e.g. `--accent: #6366f1;` → `--accent: #059669;`
- **Restart:** none (Vite hot-reloads CSS).

## Port (backend)

- **File:** `backend/.env` → `PORT=8000`
- Also update `frontend/vite.config.ts`'s proxy `target` to match.
- **Restart:** both backend and frontend dev server.

## Backend URL the frontend talks to (non-dev deployment)

- **File:** `frontend/.env` (create it) → `VITE_API_BASE_URL=http://your-backend-host:8000`
- **Restart:** rebuild the frontend (`npm run build`).

## Model path (checkpoints)

- **File:** `backend/.env` → `OPENVOICE_CHECKPOINT_DIR=...`
- **Restart:** backend.

## CPU/GPU mode

- **File:** `backend/.env` → `DEVICE=auto|cpu|cuda:0`
- **Restart:** backend.

## Generation settings supported by the model

MeloTTS/OpenVoice currently exposes **speed** (already wired up as the
`speed` field on `POST /api/voices/{id}/generate`, defaulting to 1.0, range
0.5-2.0 — see `GenerateRequest` in `backend/app/schemas/generation.py`). No
other generation parameters (pitch, emotion, etc.) are exposed by this model
version; adding a UI control for one that doesn't exist would be a fake
feature, which this project deliberately avoids.
