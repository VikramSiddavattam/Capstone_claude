"""Shared pytest fixtures.

Integration tests use fixture HTML files and a local ``http.server``
instance only — never a live public website (impl-plan Epic 8.1 / approved
requirements: "no live website testing").
"""

from __future__ import annotations

import functools
import http.server
import threading
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


class _FixtureHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):  # silence request logging in test output
        pass


@pytest.fixture(scope="session")
def fixture_server():
    """Serve ``tests/fixtures`` over plain HTTP on localhost for URL-mode
    integration tests (Playwright navigates to this local server)."""
    handler = functools.partial(_FixtureHTTPRequestHandler, directory=str(FIXTURES_DIR))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
