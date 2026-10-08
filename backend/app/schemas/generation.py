from datetime import datetime

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str = Field(min_length=1)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    pitch: float = Field(default=0.0, ge=-50.0, le=50.0)
    format: str = Field(default="wav")


class GenerationRecord(BaseModel):
    id: str
    voice_id: str
    voice_name: str
    created_at: datetime
    text_preview: str
    full_text_chars: int
    audio_url: str
    duration_seconds: float | None = None
    chunk_count: int = 1


class GenerationList(BaseModel):
    generations: list[GenerationRecord]
