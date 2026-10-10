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

    # --- Fish Audio TTS ---
    TTS_VOICE_KEYS: tuple[str, ...] = (
        "motivation",
        "news",
        "hindi_yuva",
        "hindi_energetic",
        "adrian",
        "ethan",
    )
    TTS_DEFAULT_VOICE_KEY: str = "motivation"
    TTS_MAX_TEXT_LENGTH: int = 1000
    FISH_TTS_MAX_CHARS: int = int(os.getenv("FISH_TTS_MAX_CHARS", str(TTS_MAX_TEXT_LENGTH)))

    FISH_API_KEY: str = os.getenv("FISH_API_KEY", "")
    FISH_VOICE_ID: str = os.getenv("FISH_VOICE_ID", "")
    FISH_TTS_MODEL: str = os.getenv("FISH_TTS_MODEL", "s2.1-pro-free")
    FISH_VOICE_MOTIVATION: str = os.getenv("FISH_VOICE_MOTIVATION", "")
    FISH_VOICE_NEWS: str = os.getenv("FISH_VOICE_NEWS", "")
    FISH_VOICE_HINDI_YUVA: str = os.getenv("FISH_VOICE_HINDI_YUVA", "d4d1b40efad24801a84d1e78517866f8")
    FISH_VOICE_HINDI_ENERGETIC: str = os.getenv("FISH_VOICE_HINDI_ENERGETIC", "e68315c9dd2f498aab485b813e3fda6d")
    FISH_VOICE_ADRIAN: str = os.getenv("FISH_VOICE_ADRIAN", "bf322df2096a46f18c579d0baa36f41d")
    FISH_VOICE_ETHAN: str = os.getenv("FISH_VOICE_ETHAN", "536d3a5e000945adb7038665781a4aca")

    # --- Uploads ---
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    MIN_REFERENCE_SECONDS: float = float(os.getenv("MIN_REFERENCE_SECONDS", "3"))
    MAX_REFERENCE_SECONDS: float = float(os.getenv("MAX_REFERENCE_SECONDS", "180"))

    def ensure_dirs(self) -> None:
        for d in (self.DATA_DIR, self.VOICES_DIR, self.GENERATED_DIR, self.TEMP_DIR, self.CACHE_DIR, self.PREVIEWS_DIR):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
