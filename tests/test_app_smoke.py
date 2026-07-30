from __future__ import annotations

import runpy
from pathlib import Path

PROJECT_ROOT = Path(__file__).parents[1]


def test_marimo_app_imports_without_running_a_server() -> None:
    namespace = runpy.run_path(str(PROJECT_ROOT / "app.py"), run_name="cew_app")

    assert "app" in namespace


def test_wasm_export_declares_runtime_dependencies_and_src_import_root() -> None:
    app_source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
    marimo_config = (PROJECT_ROOT / ".marimo.toml").read_text(encoding="utf-8")

    for package in ("marimo", "numpy", "scikit-learn", "scipy"):
        assert f'"{package}==' in app_source
    assert 'pythonpath = ["src"]' in marimo_config
