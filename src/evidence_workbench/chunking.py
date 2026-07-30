"""Deterministic, exact-offset document chunking."""

from __future__ import annotations

import re
from hashlib import sha256

from .domain import Chunk, ChunkConfig, ChunkCorpus, DocumentCorpus
from .text import normalize_text, stable_hash
from .validation import validate_documents

_BREAK_MARKERS = ("\n\n", "\n", ". ", "; ", ", ", " ")
MAX_CHUNKS = 2_000


def _choose_end(text: str, start: int, config: ChunkConfig) -> int:
    hard_end = min(start + config.max_chars, len(text))
    if hard_end == len(text):
        return hard_end
    minimum = start + int(config.max_chars * config.min_break_fraction)
    for marker in _BREAK_MARKERS:
        boundary = text.rfind(marker, minimum, hard_end)
        if boundary >= minimum:
            return boundary + len(marker)
    return hard_end


def _chunk_entities(text: str, entities: tuple[str, ...]) -> tuple[str, ...]:
    normalized = normalize_text(text)
    return tuple(
        sorted(
            entity
            for entity in entities
            if re.search(
                rf"(?<!\w){re.escape(normalize_text(entity))}(?!\w)",
                normalized,
            )
            is not None
        )
    )


def chunk_documents(corpus: DocumentCorpus, config: ChunkConfig) -> ChunkCorpus:
    """Create stable overlapping chunks while preserving exact source spans."""
    validated = validate_documents(corpus)
    chunks: list[Chunk] = []
    for document in validated.documents:
        start = 0
        while start < len(document.text):
            if len(chunks) >= MAX_CHUNKS:
                raise ValueError(f"chunk limit exceeds the {MAX_CHUNKS} chunk maximum")
            end = _choose_end(document.text, start, config)
            if end <= start:
                raise RuntimeError("chunking failed to advance")
            source_text = document.text[start:end]
            content_hash = sha256(source_text.encode("utf-8")).hexdigest()
            identity_hash = stable_hash(document.document_id, str(start), str(end), content_hash)
            chunks.append(
                Chunk(
                    chunk_id=f"{document.document_id}:{start}-{end}:{identity_hash[:12]}",
                    document_id=document.document_id,
                    title=document.title,
                    source_url=document.source_url,
                    published_on=document.published_on,
                    start_offset=start,
                    end_offset=end,
                    text=source_text,
                    normalized_text=normalize_text(source_text),
                    content_sha256=content_hash,
                    entities=_chunk_entities(source_text, document.entities),
                )
            )
            if end == len(document.text):
                break
            next_start = end - config.overlap_chars
            start = next_start if next_start > start else end

    digest = stable_hash(
        str(config.max_chars),
        str(config.overlap_chars),
        str(config.min_break_fraction),
        *(chunk.chunk_id for chunk in chunks),
    )
    return ChunkCorpus(chunks=tuple(chunks), corpus_digest=digest, config=config)
