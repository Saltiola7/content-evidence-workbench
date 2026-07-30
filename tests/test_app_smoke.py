from __future__ import annotations

import runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]
APP_PATH = PROJECT_ROOT / "src" / "app.py"


def test_marimo_app_imports_without_running_a_server() -> None:
    namespace = runpy.run_path(str(APP_PATH), run_name="cew_app")

    assert "app" in namespace


def test_wasm_export_declares_runtime_dependencies() -> None:
    app_source = APP_PATH.read_text(encoding="utf-8")

    for package in ("marimo", "numpy", "scikit-learn", "scipy"):
        assert f'"{package}==' in app_source


def test_notebook_is_colocated_with_the_importable_package() -> None:
    marimo_config = (PROJECT_ROOT / ".marimo.toml").read_text(encoding="utf-8")

    assert APP_PATH.is_file()
    assert (APP_PATH.parent / "evidence_workbench" / "__init__.py").is_file()
    assert 'pythonpath = ["src"]' in marimo_config
