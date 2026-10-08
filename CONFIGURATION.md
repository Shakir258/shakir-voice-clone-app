# Configuration

Central settings live in `backend/app/config.py`, driven by `backend/.env`
(copy `backend/.env.example` to `backend/.env` and edit that — don't edit
`config.py` for machine-specific values).

| Setting | File | Current value | What to put | Required? | Example |
|---|---|---|---|---|---|
| Backend host | `backend/.env` (`HOST`) | `127.0.0.1` | Leave as-is unless you need LAN access | May change | `0.0.0.0` |
| Backend port | `backend/.env` (`PORT`) | `8000` | Any free port | May change | `8001` |
| Allowed frontend origins | `backend/.env` (`CORS_ORIGINS`) | `http://localhost:5173` | Must match wherever the frontend is served from | Must change if you change the frontend port/host | `http://localhost:5174` |
| Model checkpoint folder | `backend/.env` (`OPENVOICE_CHECKPOINT_DIR`) | `./models/checkpoints_v2` | Where you extracted OpenVoice's `checkpoints_v2.zip` | **Must set** if you put it anywhere else | `D:/models/checkpoints_v2` |
| MeloTTS language | `backend/.env` (`MELO_LANGUAGE`) | `EN` | `EN`, `ES`, `FR`, `ZH`, `JP`, `KR` | May change | `ES` |
| MeloTTS base speaker | `backend/.env` (`MELO_SPEAKER`) | `EN-Default` | Must exist for the chosen language (see MeloTTS docs) | May change | `EN-US` |
| CPU/GPU device | `backend/.env` (`DEVICE`) | `auto` | `auto`, `cpu`, or `cuda:0` | May change | `cuda:0` |
| Watermarking | `backend/.env` (`ENABLE_WATERMARK`) | `false` | `true` to embed OpenVoice's inaudible watermark | May change | `true` |
| Max characters per chunk | `backend/.env` (`MAX_CHARS_PER_CHUNK`) | `350` | Lower = more, shorter chunks; affects pacing at chunk boundaries | Should not need to change | `250` |
| Max characters per generation | `backend/.env` (`MAX_TOTAL_CHARS`) | `5000` | Upper bound on one generate request | May change | `10000` |
| Max upload size (MB) | `backend/.env` (`MAX_UPLOAD_MB`) | `25` | Recording/upload size cap | May change | `50` |
| Min/max reference length (s) | `backend/.env` (`MIN_REFERENCE_SECONDS` / `MAX_REFERENCE_SECONDS`) | `3` / `180` | How short/long a reference recording may be | Should not need to change | `5` / `120` |
| Frontend API base URL | `frontend/.env` (`VITE_API_BASE_URL`) | *(unset — uses Vite's dev proxy)* | Only set this if you serve the built frontend separately from the backend | Must set for a production/non-dev deployment | `http://192.168.1.20:8000` |
| Frontend dev port / backend proxy target | `frontend/vite.config.ts` | `5173` / `http://127.0.0.1:8000` | Match your backend's actual host/port | Must change if backend HOST/PORT changed | `target: "http://127.0.0.1:8001"` |

**Values you should NOT change:** the API route paths in
`backend/app/api/*.py` and the corresponding paths in
`frontend/src/services/*Api.ts` — they must match each other. If you rename a
route on one side, update the other.

Restart requirement: any `.env` change requires restarting the backend
(`uvicorn`). `vite.config.ts` changes require restarting the frontend dev
server (`npm run dev`).
