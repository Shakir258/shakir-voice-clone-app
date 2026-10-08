import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.generation import GenerateRequest, GenerationList, GenerationRecord
from app.services import history_service as history
from app.services import tts_service
from app.services import voice_profile_service as voices
from app.services.model_service import ModelNotReadyError
from app.utils.files import assert_safe_id
from app.utils.ids import new_id

logger = logging.getLogger(__name__)
router = APIRouter(tags=["generations"])


@router.post("/api/voices/{voice_id}/generate", response_model=GenerationRecord, status_code=201)
def generate(voice_id: str, body: GenerateRequest) -> GenerationRecord:
    try:
        voice_meta = voices.get_voice(voice_id)
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")

    text = body.text.strip()
    if not text:
        raise HTTPException(400, "Text must not be empty.")

    generation_id = new_id("gen")
    out_path: Path = settings.GENERATED_DIR / f"{generation_id}.wav"

    try:
        duration, chunk_count = tts_service.generate_speech(
            voice_id, text, speed=body.speed, out_path=out_path, pitch=body.pitch, format=body.format
        )
    except tts_service.TextTooLongError as exc:
        raise HTTPException(400, str(exc))
    except ModelNotReadyError as exc:
        raise HTTPException(503, str(exc))
    except FileNotFoundError as exc:
        # e.g. se.pth missing -> profile needs recompute
        raise HTTPException(409, str(exc))
    except Exception as exc:  # noqa: BLE001
        logger.exception("Generation failed")
        raise HTTPException(
            500,
            "Voice generation failed unexpectedly. Check the backend logs "
            "for details.",
        ) from exc

    preview = text[:140] + ("…" if len(text) > 140 else "")
    record = {
        "id": generation_id,
        "voice_id": voice_id,
        "voice_name": voice_meta["name"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "text_preview": preview,
        "full_text_chars": len(text),
        "audio_url": f"/api/generations/{generation_id}/audio",
        "duration_seconds": duration,
        "chunk_count": chunk_count,
    }
    history.add_record(record)
    return GenerationRecord(**record)


@router.get("/api/generations", response_model=GenerationList)
def list_generations() -> GenerationList:
    return GenerationList(generations=history.list_records())


@router.get("/api/generations/{generation_id}")
def get_generation(generation_id: str) -> GenerationRecord:
    record = history.get_record(generation_id)
    if record is None:
        raise HTTPException(404, "Generation not found.")
    return GenerationRecord(**record)


@router.get("/api/generations/{generation_id}/audio")
def get_generation_audio(generation_id: str):
    assert_safe_id(generation_id)
    path = settings.GENERATED_DIR / f"{generation_id}.wav"
    if not path.exists():
        raise HTTPException(404, "Audio file not found.")
    return FileResponse(path, media_type="audio/wav", filename=f"{generation_id}.wav")


@router.delete("/api/generations/{generation_id}", status_code=204)
def delete_generation(generation_id: str) -> None:
    if not history.delete_record(generation_id):
        raise HTTPException(404, "Generation not found.")
