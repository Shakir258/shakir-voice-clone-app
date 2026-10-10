from fastapi import APIRouter

from app.schemas.common import HealthResponse, ModelStatusResponse
from app.services.model_service import model_service

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/api/model/status", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    return ModelStatusResponse(
        status="ready",
        device=model_service.device,
        detail=None,
    )
