from app.services.tts_service import split_into_chunks


def test_short_text_single_chunk():
    text = "Hello there."
    assert split_into_chunks(text, max_chars=100) == [text]


def test_empty_text_no_chunks():
    assert split_into_chunks("", max_chars=100) == []


def test_long_text_splits_at_sentence_boundaries():
    text = "One. Two. Three. Four. Five."
    chunks = split_into_chunks(text, max_chars=10)
    assert "".join(chunks).replace(" ", "") == text.replace(" ", "")
    for c in chunks:
        # Sentences here are short enough that no chunk should exceed the
        # limit by more than a single short sentence's worth of slack.
        assert len(c) <= 12


def test_never_splits_mid_word():
    text = "Supercalifragilisticexpialidocious is a very long single word indeed."
    chunks = split_into_chunks(text, max_chars=10)
    rejoined = " ".join(chunks)
    assert "Supercalifragilisticexpialidocious" in rejoined


def test_hindi_purna_viram_chunking():
    hindi_text = "भारत एक विशाल और सुंदर देश है। यहाँ विभिन्न संस्कृतियों का संगम है। अनेकता में एकता हमारी पहचान है।"
    chunks = split_into_chunks(hindi_text, max_chars=40)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 45
    # Verify no characters were lost
    assert "भारत" in chunks[0]
    assert "पहचान" in chunks[-1]


def test_deterministic_audio_cache(tmp_path, monkeypatch):
    from app.services.cache_service import get_cached_audio, store_cached_audio
    from app.config import settings

    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path / "cache")
    text = "नमस्ते, यह एक टेस्ट ऑडियो है।"
    voice_id = "hi-male-news-anchor-01"

    assert get_cached_audio(text, voice_id, speed=1.0) is None

    fake_audio = tmp_path / "sample.wav"
    fake_audio.write_bytes(b"RIFF" + b"\x00" * 600)  # > 512 bytes

    store_cached_audio(fake_audio, text, voice_id, speed=1.0)
    cached = get_cached_audio(text, voice_id, speed=1.0)
    assert cached is not None
    assert cached.exists()
    assert cached.stat().st_size == fake_audio.stat().st_size
