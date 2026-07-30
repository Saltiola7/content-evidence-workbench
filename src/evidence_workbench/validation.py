"""Bounded, non-retaining validation for documents and visitor files."""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Mapping, Sequence
from datetime import date
from io import StringIO
from pathlib import Path
from urllib.parse import urlparse

from .domain import Document, DocumentCorpus
from .text import stable_hash

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DOCUMENTS = 250
MAX_ENTITIES_PER_DOCUMENT = 32


class DocumentValidationError(ValueError):
    """Actionable validation error that never includes visitor content."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.partial_corpus: None = None


def _error(code: str, message: str) -> DocumentValidationError:
    return DocumentValidationError(code, message)


def _as_nonempty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise _error(f"empty_{field}", f"{field} must be a nonempty string")
    return value


def _validate_utf8(value: str) -> None:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _error("invalid_utf8", "document text must be valid UTF-8") from exc


def _validate_source_url(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise _error("source_url_type", "source_url must be an HTTP(S) string")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise _error("source_url_scheme", "source_url must use HTTP or HTTPS")
    return value


def _validate_date(value: object) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise _error("published_on_type", "published_on must be an ISO date")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise _error("published_on_format", "published_on must be an ISO date") from exc
    return value


def _validate_entities(value: object) -> tuple[str, ...]:
    if value is None or value == "":
        return ()
    if isinstance(value, str):
        candidates: Sequence[object] = [item for item in value.split("|") if item]
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        candidates = value
    else:
        raise _error("entities_type", "entities must be a list or pipe-delimited string")
    if len(candidates) > MAX_ENTITIES_PER_DOCUMENT:
        raise _error(
            "entity_limit",
            f"entity count exceeds the {MAX_ENTITIES_PER_DOCUMENT} per-document limit",
        )
    entities: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            raise _error("entity_label", "entity labels must be nonempty strings")
        entities.append(candidate.strip())
    return tuple(dict.fromkeys(entities))


def _record_to_document(record: object) -> Document:
    if isinstance(record, Document):
        record = {
            "document_id": record.document_id,
            "title": record.title,
            "text": record.text,
            "source_url": record.source_url,
            "published_on": record.published_on,
            "entities": record.entities,
        }
    if not isinstance(record, Mapping):
        raise _error("record_type", "each document must be a mapping")
    document_id = _as_nonempty_string(record.get("document_id"), field="document_id").strip()
    title = _as_nonempty_string(record.get("title"), field="title").strip()
    text = _as_nonempty_string(record.get("text"), field="text")
    _validate_utf8(text)
    return Document(
        document_id=document_id,
        title=title,
        text=text,
        source_url=_validate_source_url(record.get("source_url")),
        published_on=_validate_date(record.get("published_on")),
        entities=_validate_entities(record.get("entities")),
    )


def validate_documents(records: object) -> DocumentCorpus:
    """Validate all records before exposing a corpus; never return partial state."""
    if isinstance(records, DocumentCorpus):
        candidates: object = records.documents
    else:
        candidates = records
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes, bytearray)):
        raise _error("records_type", "records must be a sequence of documents")
    if not candidates:
        raise _error("empty_corpus", "at least one document is required")
    if len(candidates) > MAX_DOCUMENTS:
        raise _error("document_limit", f"document count exceeds the {MAX_DOCUMENTS} limit")

    documents: list[Document] = []
    identities: set[str] = set()
    byte_size = 0
    for candidate in candidates:
        document = _record_to_document(candidate)
        if document.document_id in identities:
            raise _error("duplicate_document_id", "document identities must be unique")
        identities.add(document.document_id)
        byte_size += len(document.text.encode("utf-8"))
        if byte_size > MAX_UPLOAD_BYTES:
            raise _error("byte_limit", "document text exceeds the 5 MB limit")
        documents.append(document)
    return DocumentCorpus(tuple(documents))


def _upload_identity(filename: str, text: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.casefold()).strip("-") or "document"
    return f"{stem}-{stable_hash(filename, text)[:10]}"


def _mapped_record(
    record: Mapping[str, object],
    mapping: Mapping[str, str],
) -> dict[str, object]:
    required = {"document_id", "title", "text"}
    if not required.issubset(mapping):
        raise _error("mapping_fields", "mapping must define document_id, title, and text")
    mapped: dict[str, object] = {}
    for target in (
        "document_id",
        "title",
        "text",
        "source_url",
        "published_on",
        "entities",
    ):
        source = mapping.get(target)
        if source is not None:
            if source not in record:
                raise _error("mapping_column", "a mapped column is missing from the upload")
            mapped[target] = record[source]
    return mapped


def parse_upload(
    filename: str,
    data: bytes,
    *,
    mapping: Mapping[str, str] | None = None,
) -> DocumentCorpus:
    """Parse a supported bounded file without fetching URLs or retaining bytes."""
    if not isinstance(data, bytes):
        raise _error("upload_type", "upload data must be bytes")
    if len(data) > MAX_UPLOAD_BYTES:
        raise _error("byte_limit", "upload exceeds the 5 MB limit")
    try:
        decoded = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _error("invalid_utf8", "upload must be valid UTF-8") from exc

    suffix = Path(filename).suffix.casefold()
    if suffix in {".txt", ".md", ".markdown"}:
        title = (
            Path(filename).stem.replace("-", " ").replace("_", " ").strip() or "Uploaded document"
        )
        if suffix in {".md", ".markdown"}:
            heading = next(
                (
                    line.lstrip("#").strip()
                    for line in decoded.splitlines()
                    if line.startswith("#") and line.lstrip("#").strip()
                ),
                None,
            )
            title = heading or title
        return validate_documents(
            [
                {
                    "document_id": _upload_identity(filename, decoded),
                    "title": title,
                    "text": decoded,
                }
            ]
        )

    if suffix not in {".csv", ".json"}:
        raise _error(
            "unsupported_type",
            "supported uploads are UTF-8 text, Markdown, CSV, and JSON",
        )
    if mapping is None:
        raise _error("mapping_required", "CSV and JSON uploads require an explicit field mapping")

    if suffix == ".csv":
        source_records: object = list(csv.DictReader(StringIO(decoded)))
    else:
        try:
            source_records = json.loads(decoded)
        except json.JSONDecodeError as exc:
            raise _error("json_syntax", "JSON upload is not valid JSON") from exc
    if not isinstance(source_records, list):
        raise _error("structured_shape", "structured upload must contain a list of records")
    mapped_records: list[dict[str, object]] = []
    for record in source_records:
        if not isinstance(record, Mapping):
            raise _error("record_type", "each document must be a mapping")
        mapped_records.append(_mapped_record(record, mapping))
    return validate_documents(mapped_records)
