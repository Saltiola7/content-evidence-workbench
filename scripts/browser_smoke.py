"""Exercise the built WASM application in a real browser."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import threading
import time
from pathlib import Path

from playwright.sync_api import ConsoleMessage, Page, sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """Serve an export without adding request noise to CI logs."""

    def log_message(self, format: str, *args: object) -> None:
        return


def _serve(root: Path) -> tuple[http.server.ThreadingHTTPServer, str]:
    handler = functools.partial(QuietHandler, directory=str(root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, f"http://{host}:{port}/"


def _exercise(page: Page, url: str) -> None:
    console_errors: list[str] = []
    page_errors: list[str] = []

    def capture_console(message: ConsoleMessage) -> None:
        if message.type == "error":
            console_errors.append(message.text)

    page.on("console", capture_console)
    page.on("pageerror", lambda error: page_errors.append(str(error)))
    page.goto(url, wait_until="domcontentloaded", timeout=180_000)

    page.get_by_role("heading", name="Content Evidence Workbench", level=1).wait_for(
        state="visible",
        timeout=180_000,
    )
    expected = page.get_by_text(
        "Aster Labs Energy Handbook - Edition 1",
        exact=False,
    ).first
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        query = page.get_by_role("textbox", name="Describe the evidence you need")
        query.fill("solar battery evidence")
        query.press("Enter")
        try:
            expected.wait_for(state="visible", timeout=10_000)
            break
        except PlaywrightTimeoutError:
            page.wait_for_timeout(5_000)
    else:
        raise RuntimeError("WASM worker did not recompute the evidence query")

    if page.locator("h1").count() != 1:
        raise RuntimeError("browser demo must expose exactly one level-one heading")
    if page.locator("table:not(:has(caption))").count():
        raise RuntimeError("browser demo contains a table without a caption")
    if console_errors or page_errors:
        raise RuntimeError(f"browser errors: console={console_errors!r}; page={page_errors!r}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export_root", type=Path)
    args = parser.parse_args()
    root = args.export_root.resolve()
    server, url = _serve(root)
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                _exercise(page, url)
            finally:
                browser.close()
    finally:
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()
    print("browser interaction smoke passed")


if __name__ == "__main__":
    main()
