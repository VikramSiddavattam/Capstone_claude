"""FastAPI route-level integration tests via TestClient.

URL-mode routing is exercised against the local fixture server (never a
live site); raw-HTML mode is exercised via multipart/form-encoded POSTs,
matching the actual Component 1 -> Component 2 contract.
"""

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import read_fixture

client = TestClient(app)


def test_get_form_returns_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "<form" in resp.text


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_analyze_raw_html_text_success():
    resp = client.post(
        "/analyze",
        data={"mode": "raw_html", "html_text": read_fixture("basic_elements.html")},
    )
    assert resp.status_code == 200
    assert "Analysis Report" in resp.text


def test_analyze_raw_html_file_upload_success():
    content = read_fixture("basic_elements.html").encode("utf-8")
    resp = client.post(
        "/analyze",
        data={"mode": "raw_html"},
        files={"html_file": ("page.html", content, "text/html")},
    )
    assert resp.status_code == 200
    assert "Analysis Report" in resp.text


def test_analyze_invalid_mode_returns_422():
    resp = client.post("/analyze", data={"mode": "bogus"})
    assert resp.status_code == 422


def test_analyze_raw_html_missing_content_returns_400():
    resp = client.post("/analyze", data={"mode": "raw_html"})
    assert resp.status_code == 400
    assert "Provide HTML text" in resp.text


def test_analyze_url_missing_url_returns_400():
    resp = client.post("/analyze", data={"mode": "url"})
    assert resp.status_code == 400


def test_analyze_url_invalid_scheme_returns_400():
    resp = client.post("/analyze", data={"mode": "url", "url": "ftp://example.com"})
    assert resp.status_code == 400
    assert "scheme" in resp.text.lower()


def test_analyze_no_elements_returns_actionable_400():
    resp = client.post(
        "/analyze", data={"mode": "raw_html", "html_text": read_fixture("no_elements.html")}
    )
    assert resp.status_code == 400
    assert "No matching elements" in resp.text


def test_analyze_url_mode_end_to_end(fixture_server):
    resp = client.post(
        "/analyze", data={"mode": "url", "url": f"{fixture_server}/basic_elements.html"}
    )
    assert resp.status_code == 200
    assert "Analysis Report" in resp.text
