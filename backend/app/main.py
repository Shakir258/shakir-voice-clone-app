from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_generations, routes_health, routes_voices
from app.config import settings
from app.services.model_service import model_service
from app.utils.files import UnsafeIdentifierError
from app.utils.logging import configure_logging

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model stack once, at startup, in the background thread
    # FastAPI's startup runs in. If this fails (e.g. missing
    # checkpoints), the API still comes up - /api/model/status reports
    # the error and every generation endpoint returns a clear 503
    # instead of the process crashing.
    model_service.load()
    yield


app = FastAPI(title="Personal Voice Clone TTS", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(UnsafeIdentifierError)
async def unsafe_id_handler(request: Request, exc: UnsafeIdentifierError):
    return JSONResponse(status_code=400, content={"error": "Invalid identifier."})


app.include_router(routes_health.router)
app.include_router(routes_voices.router)
app.include_router(routes_generations.router)
