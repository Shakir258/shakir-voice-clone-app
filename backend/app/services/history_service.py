"""
Generation history, stored as a single JSON file
(data/history.json). Simple on purpose: this is a personal single-user
app, so a real database (SQLite/Postgres) would be more machinery than
the problem needs. A basic file lock avoids corruption from concurrent
writes within one process.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from app.config import settings

_lock = threading.Lock()


def _load() -> list[dict]:
    if not settings.HISTORY_FILE.exists():
        return []
    try:
        return json.loads(settings.HISTORY_FILE.read_text())
    except json.JSONDecodeError:
        return []


def _save(records: list[dict]) -> None:
    settings.HISTORY_FILE.write_text(json.dumps(records, indent=2))


def add_record(record: dict) -> None:
    with _lock:
        records = _load()
        records.insert(0, record)
        _save(records)


def list_records(limit: int = 100) -> list[dict]:
    with _lock:
        return _load()[:limit]


def get_record(generation_id: str) -> dict | None:
    with _lock:
        for r in _load():
            if r["id"] == generation_id:
                return r
    return None


def delete_record(generation_id: str) -> bool:
    with _lock:
        records = _load()
        remaining = [r for r in records if r["id"] != generation_id]
        if len(remaining) == len(records):
            return False
        _save(remaining)
    audio_path = Path(settings.GENERATED_DIR) / f"{generation_id}.wav"
    audio_path.unlink(missing_ok=True)
    return True
