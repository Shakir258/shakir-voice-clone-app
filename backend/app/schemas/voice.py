from datetime import datetime

from pydantic import BaseModel, Field


class VoiceProfile(BaseModel):
    id: str
    name: str
    created_at: datetime
    ready: bool
    duration_seconds: float | None = None
    is_preset: bool = False
    gender: str | None = None
    category: str | None = None
    style: str | None = None
    description: str | None = None
    engine: str | None = None
    tags: list[str] = Field(default_factory=list)
    preview_text: str | None = None



class VoiceProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class VoiceProfileList(BaseModel):
    voices: list[VoiceProfile]
