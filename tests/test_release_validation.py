from __future__ import annotations

import json
import runpy
from copy import deepcopy
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[1]
validate_static_session = runpy.run_path(
    str(PROJECT_ROOT / "scripts" / "validate_static_session.py")
)["validate_static_session"]


def _session() -> dict[str, object]:
    return {
        "version": "1",
        "metadata": {
            "marimo_version": "0.23.15",
            "script_metadata_hash": "source-hash",
        },
        "cells": [
            {
                "id": "intro",
                "code_hash": "cell-hash",
                "outputs": [
                    {
                        "type": "data",
                        "data": {
                            "text/html": (
                                "<h1>Content Evidence Workbench</h1>"
                                "<marimo-ui-element random-id='first'>"
                                "Synthetic corpus"
                                "</marimo-ui-element>"
                            )
                        },
                    }
                ],
                "console": [],
            }
        ],
    }


def _write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_static_session_allows_only_generated_ui_ids(tmp_path: Path) -> None:
    committed = _session()
    generated = deepcopy(committed)
    generated["cells"][0]["outputs"][0]["data"]["text/html"] = (  # type: ignore[index]
        "<h1>Content Evidence Workbench</h1>"
        "<marimo-ui-element random-id='second'>"
        "Synthetic corpus"
        "</marimo-ui-element>"
    )
    committed_path = tmp_path / "committed.json"
    generated_path = tmp_path / "generated.json"
    _write(committed_path, committed)
    _write(generated_path, generated)

    validate_static_session(committed_path, generated_path)


def test_static_session_rejects_meaningful_output_drift(tmp_path: Path) -> None:
    committed = _session()
    generated = deepcopy(committed)
    generated["cells"][0]["outputs"][0]["data"]["text/html"] += "changed"  # type: ignore[index]
    committed_path = tmp_path / "committed.json"
    generated_path = tmp_path / "generated.json"
    _write(committed_path, committed)
    _write(generated_path, generated)

    with pytest.raises(RuntimeError, match="differs"):
        validate_static_session(committed_path, generated_path)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("console", [{"type": "stderr", "text": "warning"}], "console output"),
        (
            "output",
            "Traceback (most recent call last)",
            "Traceback",
        ),
    ],
)
def test_static_session_rejects_runtime_failures(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    committed = _session()
    generated = deepcopy(committed)
    if field == "console":
        generated["cells"][0]["console"] = value  # type: ignore[index]
    else:
        generated["cells"][0]["outputs"][0]["data"]["text/html"] += value  # type: ignore[index,operator]
    committed_path = tmp_path / "committed.json"
    generated_path = tmp_path / "generated.json"
    _write(committed_path, committed)
    _write(generated_path, generated)

    with pytest.raises(RuntimeError, match=message):
        validate_static_session(committed_path, generated_path)
