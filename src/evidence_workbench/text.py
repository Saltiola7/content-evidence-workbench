"""Pure text normalization and identity helpers."""

from __future__ import annotations

import re
import unicodedata
from hashlib import sha256

_WHITESPACE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Normalize text for retrieval without modifying source text."""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return _WHITESPACE.sub(" ", normalized).strip()


def stable_hash(*parts: str) -> str:
    payload = "\0".join(parts).encode("utf-8")
    return sha256(payload).hexdigest()
