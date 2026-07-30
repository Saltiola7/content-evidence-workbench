"""Fail closed when a Marimo WASM export is incomplete or mispackaged."""

from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

ERROR_MARKERS = (
    "MarimoExceptionRaisedError",
    "CellNotInitializedError",
    "No module named",
    "Traceback (most recent call last)",
)
TEXT_SUFFIXES = {".html", ".json", ".py"}


def validate_export(export_root: Path) -> None:
    """Validate the executable shell, embedded outputs, and local package wheel."""

    if not (export_root / "index.html").is_file():
        raise RuntimeError("WASM export is missing index.html")

    for path in sorted(export_root.rglob("*")):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in ERROR_MARKERS:
            if marker in text:
                raise RuntimeError(f"WASM export contains {marker!r} in {path}")
        if "/Users/" in text:
            raise RuntimeError(f"WASM export contains a private local path in {path}")

    wheels = sorted((export_root / "public" / "wheels").glob("*.whl"))
    matching: list[Path] = []
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            names = set(archive.namelist())
        if "evidence_workbench/__init__.py" in names:
            matching.append(wheel)
        if any(name.startswith("src/evidence_workbench/") for name in names):
            raise RuntimeError(f"WASM export contains malformed src-layout wheel: {wheel}")

    if len(matching) != 1:
        raise RuntimeError(
            "WASM export must contain exactly one importable evidence_workbench wheel"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_root", type=Path)
    args = parser.parse_args()
    validate_export(args.export_root.resolve())
    print("WASM package validation passed")


if __name__ == "__main__":
    main()
