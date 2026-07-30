"""Compare Marimo session exports without masking meaningful output drift."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ERROR_MARKERS = (
    "MarimoExceptionRaisedError",
    "CellNotInitializedError",
    "No module named",
    "Traceback (most recent call last)",
)
REQUIRED_MARKERS = (
    "Content Evidence Workbench",
    "Synthetic corpus",
)
_RANDOM_ID = re.compile(r"random-id='[^']+'")


def _normalize(value: Any) -> Any:
    """Remove only Marimo's nondeterministic presentation identifiers."""

    if isinstance(value, str):
        return _RANDOM_ID.sub("random-id='<generated>'", value)
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _load_session(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"invalid Marimo session {path}: {error}") from error
    if not isinstance(payload, dict):
        raise RuntimeError(f"Marimo session must be a JSON object: {path}")
    return payload


def _validate_session(payload: dict[str, Any], path: Path) -> None:
    cells = payload.get("cells")
    metadata = payload.get("metadata")
    if payload.get("version") != "1" or not isinstance(metadata, dict):
        raise RuntimeError(f"Marimo session metadata is incomplete: {path}")
    if not isinstance(metadata.get("script_metadata_hash"), str):
        raise RuntimeError(f"Marimo session lacks a script metadata hash: {path}")
    if not isinstance(cells, list) or not cells:
        raise RuntimeError(f"Marimo session has no cells: {path}")

    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for marker in ERROR_MARKERS:
        if marker in serialized:
            raise RuntimeError(f"Marimo session contains {marker!r}: {path}")
    if "/Users/" in serialized:
        raise RuntimeError(f"Marimo session contains a private local path: {path}")
    for marker in REQUIRED_MARKERS:
        if marker not in serialized:
            raise RuntimeError(f"Marimo session lacks required output {marker!r}: {path}")

    for cell in cells:
        if not isinstance(cell, dict) or not isinstance(cell.get("code_hash"), str):
            raise RuntimeError(f"Marimo session contains an invalid cell: {path}")
        console = cell.get("console")
        if not isinstance(console, list):
            raise RuntimeError(f"Marimo session cell lacks a console list: {path}")
        if console:
            raise RuntimeError(f"Marimo session contains console output: {path}")


def validate_static_session(committed_path: Path, generated_path: Path) -> None:
    """Require semantic parity while tolerating only generated UI random IDs."""

    committed = _load_session(committed_path)
    generated = _load_session(generated_path)
    _validate_session(committed, committed_path)
    _validate_session(generated, generated_path)
    if _normalize(committed) != _normalize(generated):
        raise RuntimeError(
            "committed static session differs from a fresh export beyond generated UI IDs"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("committed_session", type=Path)
    parser.add_argument("generated_session", type=Path)
    args = parser.parse_args()
    validate_static_session(
        args.committed_session.resolve(),
        args.generated_session.resolve(),
    )
    print("static session validation passed")


if __name__ == "__main__":
    main()
