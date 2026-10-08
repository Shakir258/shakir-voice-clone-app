"""
Central configuration for the backend.

Everything you are likely to need to change lives here or in `.env`
(copy `.env.example` to `.env` and edit that file — do not edit this
file directly for machine-specific values).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load variables from backend/.env if it exists.
BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    # --- Server ---
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    ]

    # --- Storage (all relative to backend/ by default) ---
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(BACKEND_DIR / "data"))).resolve()
    VOICES_DIR: Path = DATA_DIR / "voices"
    GENERATED_DIR: Path = DATA_DIR / "generated"
    TEMP_DIR: Path = DATA_DIR / "temp"
    CACHE_DIR: Path = DATA_DIR / "cache"
    PREVIEWS_DIR: Path = DATA_DIR / "previews"
    HISTORY_FILE: Path = DATA_DIR / "history.json"

    # --- Model ---
    # Preferred Hindi TTS Engine: "auto" | "indic-parler" | "piper" | "edge"
    HINDI_TTS_ENGINE: str = os.getenv("HINDI_TTS_ENGINE", "auto")
    OPENVOICE_CHECKPOINT_DIR: Path = Path(
        os.getenv("OPENVOICE_CHECKPOINT_DIR", str(BACKEND_DIR / "models" / "checkpoints_v2"))
    ).resolve()
    MELO_LANGUAGE: str = os.getenv("MELO_LANGUAGE", "EN")  # EN, ES, FR, ZH, JP, KR
    MELO_SPEAKER: str = os.getenv("MELO_SPEAKER", "EN-Default")
    DEVICE: str = os.getenv("DEVICE", "auto")  # "auto" | "cpu" | "cuda:0"
    ENABLE_WATERMARK: bool = _env_bool("ENABLE_WATERMARK", False)

    # --- Text limits ---
    # OpenVoice/MeloTTS degrades on very long single passes. We chunk
    # text longer than this many characters at sentence boundaries.
    MAX_CHARS_PER_CHUNK: int = int(os.getenv("MAX_CHARS_PER_CHUNK", "350"))
    MAX_TOTAL_CHARS: int = int(os.getenv("MAX_TOTAL_CHARS", "5000"))

    # Maximum characters accepted by the Fish Audio TTS endpoint.
    FISH_TTS_MAX_CHARS: int = int(os.getenv("FISH_TTS_MAX_CHARS", "1000"))

    # --- Fish Audio ---
    FISH_API_KEY: str = os.getenv("FISH_API_KEY", "")
    FISH_VOICE_ID: str = os.getenv("FISH_VOICE_ID", "")
    FISH_TTS_MODEL: str = os.getenv("FISH_TTS_MODEL", "s2.1-pro-free")

    # --- Uploads ---
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MIN_REFERENCE_SECONDS: float = float(os.getenv("MIN_REFERENCE_SECONDS", "3"))
    MAX_REFERENCE_SECONDS: float = float(os.getenv("MAX_REFERENCE_SECONDS", "180"))

    def ensure_dirs(self) -> None:
        for d in (self.DATA_DIR, self.VOICES_DIR, self.GENERATED_DIR, self.TEMP_DIR, self.CACHE_DIR, self.PREVIEWS_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
