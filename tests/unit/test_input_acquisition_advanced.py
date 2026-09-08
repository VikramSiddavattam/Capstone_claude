"""Additional coverage for input_acquisition's error-mapping branches,
using a mocked Playwright Page (unit-level) rather than a real browser,
since simulating a genuine TLS failure or mid-navigation abort against a
real Chromium instance is not practical/deterministic in a test suite."""

from unittest.mock import MagicMock

import pytest

from app.exceptions import (FetchTimeoutError, PageTooLargeError, RenderError,
                            TlsValidationError, TooManyRedirectsError)
from app.pipeline import input_acquisition


def test_acquire_url_maps_timeout_exception():
    page = MagicMock()
    page.goto.side_effect = Exception("Timeout 30000ms exceeded")
    with pytest.raises(FetchTimeoutError):
        input_acquisition.acquire_url(page, "https://example.com")


def test_acquire_url_maps_tls_exception():
    page = MagicMock()
    page.goto.side_effect = Exception("net::ERR_CERT_AUTHORITY_INVALID")
    with pytest.raises(TlsValidationError):
        input_acquisition.acquire_url(page, "https://example.com")


def test_acquire_url_maps_generic_render_failure():
    page = MagicMock()
    page.goto.side_effect = Exception("net::ERR_NAME_NOT_RESOLVED")
    with pytest.raises(RenderError):
        input_acquisition.acquire_url(page, "https://example.com")


def test_acquire_url_raises_page_too_large_from_route_handler():
    """Simulate the route handler having recorded a size-cap breach before
    page.goto ultimately fails/aborts navigation."""
    page = MagicMock()

    def fake_route(_matcher, handler):
        fake_request = MagicMock(resource_type="document")
        fake_route_obj = MagicMock(request=fake_request)
        fake_response = MagicMock()
        fake_response.headers.get.return_value = str(input_acquisition.MAX_BYTES + 1)
        fake_route_obj.fetch.return_value = fake_response
        handler(fake_route_obj)  # populate error_holder via the real handler
        page.goto.side_effect = Exception("net::ERR_ABORTED")

    page.route.side_effect = fake_route
    with pytest.raises(PageTooLargeError):
        input_acquisition.acquire_url(page, "https://example.com")


def test_acquire_url_raises_too_many_redirects():
    page = MagicMock()
    grandparent = MagicMock(redirected_from=None)
    parent = MagicMock(redirected_from=grandparent)
    hop1 = MagicMock(redirected_from=parent)
    hop2 = MagicMock(redirected_from=hop1)
    hop3 = MagicMock(redirected_from=hop2)
    hop4 = MagicMock(redirected_from=hop3)
    hop5 = MagicMock(redirected_from=hop4)
    hop6 = MagicMock(redirected_from=hop5)  # 6 hops > MAX_REDIRECTS (5)
    response = MagicMock(request=hop6)
    page.goto.return_value = response

    with pytest.raises(TooManyRedirectsError):
        input_acquisition.acquire_url(page, "https://example.com")


def test_route_handler_continues_non_document_requests():
    error_holder = {}
    handler = input_acquisition._make_route_handler(error_holder)
    route = MagicMock()
    route.request.resource_type = "image"
    handler(route)
    route.continue_.assert_called_once()
    route.fetch.assert_not_called()


def test_route_handler_fulfills_when_within_cap():
    error_holder = {}
    handler = input_acquisition._make_route_handler(error_holder)
    route = MagicMock()
    route.request.resource_type = "document"
    response = MagicMock()
    response.headers.get.return_value = "100"
    route.fetch.return_value = response
    handler(route)
    route.fulfill.assert_called_once_with(response=response)
    assert "error" not in error_holder


def test_route_handler_aborts_on_fetch_exception():
    error_holder = {}
    handler = input_acquisition._make_route_handler(error_holder)
    route = MagicMock()
    route.request.resource_type = "document"
    route.fetch.side_effect = Exception("network down")
    handler(route)
    route.abort.assert_called_once()
    assert isinstance(error_holder["error"], RenderError)


def test_fetch_raw_fallback_returns_degraded_page_source(fixture_server):
    page_source = input_acquisition.fetch_raw_fallback(f"{fixture_server}/basic_elements.html")
    assert page_source.degraded is True
    assert page_source.rendered is False
    assert page_source.mode == "url"
    assert "Fixture: Basic Elements" in page_source.html


def test_fetch_raw_fallback_rejects_oversized_response(fixture_server, monkeypatch):
    monkeypatch.setattr(input_acquisition, "MAX_BYTES", 10)
    with pytest.raises(PageTooLargeError):
        input_acquisition.fetch_raw_fallback(f"{fixture_server}/basic_elements.html")


def test_fetch_raw_fallback_invalid_host_raises_invalid_url_error():
    from app.exceptions import InvalidUrlError

    with pytest.raises(InvalidUrlError):
        input_acquisition.fetch_raw_fallback("https://this-host-does-not-exist.invalid")
