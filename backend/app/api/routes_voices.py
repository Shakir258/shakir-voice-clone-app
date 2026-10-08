import logging
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas.voice import VoiceProfile, VoiceProfileList, VoiceProfileUpdate
from app.services import voice_profile_service as voices
from app.services.audio_service import AudioValidationError
from app.services.model_service import ModelNotReadyError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voices", tags=["voices"])

ALLOWED_UPLOAD_TYPES = {
    "audio/webm", "video/webm", "audio/wav", "audio/x-wav", "audio/wave",
    "audio/mpeg", "audio/mp3", "audio/ogg", "audio/mp4", "audio/m4a", "audio/aac",
}


from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

@router.get("", response_model=VoiceProfileList)
def list_voices(
    include_presets: bool = Query(True, description="Include built-in and 100 studio presets"),
    category: str | None = Query(None, description="Filter by category"),
    gender: str | None = Query(None, description="Filter by gender (male/female)"),
) -> VoiceProfileList:
    return VoiceProfileList(
        voices=voices.list_voices(
            include_presets=include_presets,
            category=category,
            gender=gender,
        )
    )


@router.post("", response_model=VoiceProfile, status_code=201)
async def create_voice(name: str = Form(...), file: UploadFile = File(...)) -> VoiceProfile:
    name = name.strip()
    if not name:
        raise HTTPException(400, "Voice profile name is required.")
    if len(name) > 100:
        raise HTTPException(400, "Voice profile name is too long (max 100 characters).")

    content_type = (file.content_type or "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(
            400,
            f"Unsupported audio type '{file.content_type}'. Please record in "
            "the browser or upload a WAV/MP3/OGG/M4A file.",
        )

    settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    from app.utils.ids import new_id

    upload_path = settings.TEMP_DIR / f"upload_{new_id('tmp')}"
    size = 0
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    try:
        with open(upload_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        400, f"File too large. Maximum size is {settings.MAX_UPLOAD_MB} MB."
                    )
                f.write(chunk)

        try:
            metadata = voices.create_voice(name, upload_path)
        except AudioValidationError as exc:
            raise HTTPException(400, str(exc)) from exc
        except ModelNotReadyError as exc:
            raise HTTPException(503, str(exc)) from exc

        return VoiceProfile(**metadata)
    finally:
        upload_path.unlink(missing_ok=True)


@router.get("/{voice_id}", response_model=VoiceProfile)
def get_voice(voice_id: str) -> VoiceProfile:
    try:
        return VoiceProfile(**voices.get_voice(voice_id))
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")


@router.patch("/{voice_id}", response_model=VoiceProfile)
def rename_voice(voice_id: str, body: VoiceProfileUpdate) -> VoiceProfile:
    try:
        return VoiceProfile(**voices.rename_voice(voice_id, body.name.strip()))
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")


@router.delete("/{voice_id}", status_code=204)
def delete_voice(voice_id: str) -> None:
    try:
        voices.delete_voice(voice_id)
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")


@router.post("/{voice_id}/recompute", response_model=VoiceProfile)
def recompute_voice(voice_id: str) -> VoiceProfile:
    """Recreate the tone-color embedding from the stored reference
    recording, without requiring the user to record again."""
    try:
        return VoiceProfile(**voices.recompute_embedding(voice_id))
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")
    except AudioValidationError as exc:
        raise HTTPException(400, str(exc))
    except ModelNotReadyError as exc:
        raise HTTPException(503, str(exc))


@router.get("/{voice_id}/reference-audio")
def get_reference_audio(voice_id: str):
    from app.utils.files import assert_safe_id

    assert_safe_id(voice_id)
    path: Path = settings.VOICES_DIR / voice_id / "reference.wav"
    if not path.exists():
        raise HTTPException(404, "Reference audio not found.")
    return FileResponse(path, media_type="audio/wav")


@router.get("/{voice_id}/preview")
def get_voice_preview(voice_id: str):
    """Generate or return cached short audio preview for a voice profile."""
    from app.services import tts_service
    from app.utils.files import assert_safe_id

    assert_safe_id(voice_id)
    try:
        voice = voices.get_voice(voice_id)
    except voices.VoiceNotFoundError:
        raise HTTPException(404, "Voice profile not found.")

    settings.PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    preview_file = settings.PREVIEWS_DIR / f"{voice_id}.wav"

    if not preview_file.exists() or preview_file.stat().st_size < 512:
        sample_text = voice.get("preview_text") or "नमस्ते, यह मेरी आवाज़ का एक छोटा सा नमूना है।"
        try:
            tts_service.generate_speech(voice_id, sample_text, speed=1.0, out_path=preview_file)
        except Exception as exc:
            logger.exception("Failed to synthesize preview for %s", voice_id)
            raise HTTPException(500, f"Could not generate preview for voice {voice_id}: {exc}") from exc

    return FileResponse(preview_file, media_type="audio/wav", filename=f"{voice_id}_preview.wav")
