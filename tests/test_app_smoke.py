from __future__ import annotations

import runpy
from pathlib import Path


def test_marimo_app_imports_without_running_a_server() -> None:
    namespace = runpy.run_path(str(Path(__file__).parents[1] / "app.py"), run_name="cew_app")

    assert "app" in namespace
