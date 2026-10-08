from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str


class ModelStatusResponse(BaseModel):
    status: str  # "loading" | "ready" | "error" | "not_started"
    device: str
    detail: str | None = None
