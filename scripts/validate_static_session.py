"""Compare Marimo session exports without masking meaningful output drift."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, NamedTuple

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


class SessionIdentity(NamedTuple):
    """Source-bound identity that is stable across execution platforms."""

    version: str
    marimo_version: str
    script_metadata_hash: str
    cells: tuple[tuple[str, str], ...]


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
    for field in ("marimo_version", "script_metadata_hash"):
        if not isinstance(metadata.get(field), str):
            raise RuntimeError(f"Marimo session lacks {field!r}: {path}")
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
        if (
            not isinstance(cell, dict)
            or not isinstance(cell.get("id"), str)
            or not isinstance(cell.get("code_hash"), str)
        ):
            raise RuntimeError(f"Marimo session contains an invalid cell: {path}")
        console = cell.get("console")
        if not isinstance(console, list):
            raise RuntimeError(f"Marimo session cell lacks a console list: {path}")
        if console:
            raise RuntimeError(f"Marimo session contains console output: {path}")


def _session_identity(payload: dict[str, Any]) -> SessionIdentity:
    metadata = payload["metadata"]
    cells = payload["cells"]
    return SessionIdentity(
        version=payload["version"],
        marimo_version=metadata["marimo_version"],
        script_metadata_hash=metadata["script_metadata_hash"],
        cells=tuple((cell["id"], cell["code_hash"]) for cell in cells),
    )


def validate_static_session(committed_path: Path, generated_path: Path) -> None:
    """Require source parity and independently validate both rendered snapshots."""

    committed = _load_session(committed_path)
    generated = _load_session(generated_path)
    _validate_session(committed, committed_path)
    _validate_session(generated, generated_path)
    if _session_identity(committed) != _session_identity(generated):
        raise RuntimeError("committed static session is stale relative to the fresh source export")


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
