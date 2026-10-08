"""
User-facing error/status message strings.

Keep all strings here so they are easy to audit and translate later.
"""

# Fish Audio TTS
FISH_TTS_ENV_MISSING = (
    "Fish Audio TTS is not configured. "
    "Set FISH_API_KEY, FISH_VOICE_ID, and FISH_TTS_MODEL in your .env file."
)
FISH_TTS_TEXT_EMPTY = "Text must not be empty."
FISH_TTS_TEXT_TOO_LONG = "Text exceeds the maximum allowed length."
FISH_TTS_UPSTREAM_ERROR = "The TTS service returned an error. Please try again later."
FISH_TTS_TIMEOUT = "The TTS request timed out. Please try again."
