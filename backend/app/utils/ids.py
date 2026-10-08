import uuid


def new_id(prefix: str) -> str:
    """Generate a short, sortable-enough, collision-safe ID like 'voice_9f2a...'."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
