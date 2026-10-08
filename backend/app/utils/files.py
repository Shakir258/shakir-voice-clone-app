"""
Filesystem safety helpers.

Nothing here trusts a user-supplied path. Every ID used to build a
path is one *we* generated (see utils/ids.py), never something taken
directly from a request body or filename, which closes off path
traversal.
"""
from __future__ import annotations

import re
from pathlib import Path

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


class UnsafeIdentifierError(ValueError):
    pass


def assert_safe_id(identifier: str) -> None:
    """Raise if `identifier` is not a plain alnum/underscore/dash token."""
    if not identifier or not _SAFE_ID_RE.match(identifier):
        raise UnsafeIdentifierError(f"Unsafe identifier: {identifier!r}")


def safe_path(base: Path, identifier: str, filename: str) -> Path:
    """Build `base/identifier/filename`, asserting `identifier` is a safe token
    we generated ourselves. `filename` must be one of a small fixed set of
    names the service code chooses (never taken from user input)."""
    assert_safe_id(identifier)
    return base / identifier / filename
