"""
Devanagari-aware intelligent text chunking for Hindi speech synthesis.

Splits text along natural phonetic and sentence boundaries:
- Hindi Purna Viram (।) [\u0964]
- Deergh Viram (॥) [\u0965]
- Standard terminators (. ! ?)
- Paragraph double-breaks (\n\n)
- Clause pauses (comma, semicolon, dash) when long sentences exceed max_chars

Never splits mid-word, and protects Devanagari conjuncts (virama/halant).
"""
from __future__ import annotations

import re


# Unicode range for Devanagari is \u0900-\u097F
DEVANAGARI_REGEX = re.compile(r"[\u0900-\u097f]")

# Sentence terminators in Hindi and Western typography
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[।॥!?\.\n])\s+")

# Sub-sentence clause terminators for breaking long run-on sentences
CLAUSE_SPLIT_REGEX = re.compile(r"(?<=[,;:\-–—\u0964\u0965])\s+")


def has_hindi_script(text: str) -> bool:
    """Returns True if the string contains any Devanagari characters."""
    return bool(DEVANAGARI_REGEX.search(text))


def split_hindi_text(text: str, max_chars: int = 300) -> list[str]:
    """Intelligently chunks Hindi / multilingual text at natural sentence
    boundaries, keeping chunks below `max_chars` without cutting mid-word
    or corrupting Devanagari conjuncts."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    # First pass: split at primary sentence terminators (।, ॥, ., !, ?, newlines)
    primary_sentences = [s.strip() for s in SENTENCE_SPLIT_REGEX.split(text) if s.strip()]
    if not primary_sentences:
        primary_sentences = [text]

    chunks: list[str] = []
    current_chunk = ""

    for sentence in primary_sentences:
        # If a single sentence is larger than max_chars, split it at clause level
        if len(sentence) > max_chars:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            sub_clauses = [c.strip() for c in CLAUSE_SPLIT_REGEX.split(sentence) if c.strip()]
            if not sub_clauses or len(sub_clauses) == 1:
                # Fallback: split on whitespace words cleanly
                words = sentence.split()
                sub_current = ""
                for w in words:
                    candidate = f"{sub_current} {w}".strip() if sub_current else w
                    if len(candidate) <= max_chars:
                        sub_current = candidate
                    else:
                        if sub_current:
                            chunks.append(sub_current.strip())
                        sub_current = w
                if sub_current:
                    chunks.append(sub_current.strip())
            else:
                sub_current = ""
                for clause in sub_clauses:
                    candidate = f"{sub_current} {clause}".strip() if sub_current else clause
                    if len(candidate) <= max_chars:
                        sub_current = candidate
                    else:
                        if sub_current:
                            chunks.append(sub_current.strip())
                        sub_current = clause
                if sub_current:
                    chunks.append(sub_current.strip())
            continue

        # Normal sentence combination
        candidate = f"{current_chunk} {sentence}".strip() if current_chunk else sentence
        if len(candidate) <= max_chars:
            current_chunk = candidate
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
