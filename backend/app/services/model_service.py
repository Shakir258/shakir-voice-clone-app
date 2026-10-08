"""
Loads the TTS model stack ONCE at backend startup and exposes it to
the rest of the app. Nothing here reloads model weights per-request.

Model stack (see README "Model decision" for why):
  - MeloTTS          -> the base speaker engine that actually turns
                         text into speech audio.
  - OpenVoice V2      -> a ToneColorConverter that re-colors that
                         audio with your cloned voice's timbre
                         ("tone color"), using a small embedding
                         ("tone color embedding" / SE) extracted once
                         from your reference recording.

This is the real, documented OpenVoice V2 + MeloTTS pipeline
(https://github.com/myshell-ai/OpenVoice) - not a placeholder.
"""
from __future__ import annotations

import logging
import threading
from enum import Enum
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class ModelStatus(str, Enum):
    NOT_STARTED = "not_started"
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"


class ModelService:
    """Singleton-style holder for the loaded model objects."""

    def __init__(self) -> None:
        self.status: ModelStatus = ModelStatus.NOT_STARTED
        self.detail: str | None = None
        self.device: str = "cpu"
        self.tone_color_converter = None  # openvoice.api.ToneColorConverter
        self.base_speaker_tts = None  # melo.api.TTS
        self.default_source_se = None  # torch.Tensor
        self._lock = threading.Lock()

    def resolve_device(self) -> str:
        if settings.DEVICE != "auto":
            return settings.DEVICE
        try:
            import torch

            return "cuda:0" if torch.cuda.is_available() else "cpu"
        except Exception:  # pragma: no cover - torch always installed in prod
            return "cpu"

    def load(self) -> None:
        """Load MeloTTS + OpenVoice V2 checkpoints. Safe to call once at
        startup. Sets self.status to READY or ERROR; never raises, so a
        missing/broken model install degrades to a clear API error
        instead of crashing the server."""
        with self._lock:
            if self.status in (ModelStatus.LOADING, ModelStatus.READY):
                return
            self.status = ModelStatus.LOADING

        try:
            import gc
            import torch
            gc.collect()
            try:
                torch.set_num_threads(2)
            except Exception:
                pass

            self.device = self.resolve_device()
            logger.info("Loading TTS model stack on device=%s", self.device)

            ckpt_dir: Path = settings.OPENVOICE_CHECKPOINT_DIR
            converter_dir = ckpt_dir / "converter"
            config_path = converter_dir / "config.json"
            ckpt_path = converter_dir / "checkpoint.pth"

            if not config_path.exists() or not ckpt_path.exists():
                raise FileNotFoundError(
                    "OpenVoice V2 converter checkpoints not found at "
                    f"{converter_dir}. Download them as described in README.md "
                    "'Model setup' and set OPENVOICE_CHECKPOINT_DIR if you put "
                    "them somewhere else."
                )

            from openvoice.api import ToneColorConverter
            from melo.api import TTS as MeloTTS

            self.tone_color_converter = ToneColorConverter(
                str(config_path),
                device=self.device,
                enable_watermark=settings.ENABLE_WATERMARK,
            )
            self.tone_color_converter.load_ckpt(str(ckpt_path))

            self.base_speaker_tts = MeloTTS(
                language=settings.MELO_LANGUAGE, device=self.device
            )

            # OpenVoice ships a pre-computed "source" tone color embedding
            # per MeloTTS speaker (checkpoints_v2/base_speakers/ses/*.pth).
            # This represents MeloTTS's own voice, which is what we convert
            # *from* on the way to your cloned voice.
            speaker_key = settings.MELO_SPEAKER.lower().replace("_", "-")
            se_path = ckpt_dir / "base_speakers" / "ses" / f"{speaker_key}.pth"
            if not se_path.exists():
                raise FileNotFoundError(
                    f"Base speaker embedding not found at {se_path}. Check "
                    "MELO_SPEAKER in your .env matches an available MeloTTS speaker."
                )

            self.default_source_se = torch.load(se_path, map_location=self.device, weights_only=True)

            self.status = ModelStatus.READY
            self.detail = None
            logger.info("Model stack ready.")
        except Exception as exc:  # noqa: BLE001 - we deliberately catch everything here
            self.status = ModelStatus.ERROR
            self.detail = str(exc)
            logger.exception("Failed to load model stack")

    def require_ready(self) -> None:
        if self.status != ModelStatus.READY:
            if self.status == ModelStatus.ERROR:
                logger.info("Attempting to reload model stack...")
                self.load()
            if self.status != ModelStatus.READY:
                raise ModelNotReadyError(
                    self.detail or "The TTS model is not loaded. Check /api/model/status."
                )


class ModelNotReadyError(RuntimeError):
    pass


model_service = ModelService()
