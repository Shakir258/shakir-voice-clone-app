import shutil
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import os

os.environ.setdefault("DATA_DIR", str(BACKEND_DIR / "tests" / "_tmp_data"))

from app.config import settings  # noqa: E402


@pytest.fixture(autouse=True)
def clean_data_dir():
    settings.ensure_dirs()
    yield
    shutil.rmtree(settings.DATA_DIR, ignore_errors=True)
    settings.ensure_dirs()
