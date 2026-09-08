"""Input Acquisition Module (design-document Component 3).

Resolves user-supplied input (URL or raw HTML/upload) into a normalized
``PageSource``. Implements both impl-plan Must-Do conditions relevant to
this component:

- Must-Do #2 (URL-mode ~5MB size cap): ``page.route()`` interception on
  ``resource_type == "document"`` with a ``Content-Length`` fast path and a
  ``response.body()`` slow path, aborting before the body reaches the page.
- Redirect-count verification (Should-Do #1): counted post-navigation via
  the response's ``redirected_from`` chain, since Chromium follows
  redirects internally before Playwright's ``page.goto()`` returns.
"""

from __future__ import annotations

from urllib.parse import urlparse

import httpx

from app.exceptions import (FetchTimeoutError, InvalidUrlError,
                            PageTooLargeError, RenderError, TlsValidationError,
                            TooManyRedirectsError, UnparseableContentError)
from app.logging_config import get_logger
from app.models import PageSource

MAX_BYTES = 5 * 1024 * 1024  # ~5MB cap, Requirement/Constraint table
MAX_REDIRECTS = 5
TIMEOUT_MS = 30_000
ALLOWED_SCHEMES = {"http", "https"}

# Union CSS selector for the 8 target element types, used for marker
# injection (impl-plan Must-Do #1). querySelectorAll never descends into
# <iframe> content documents, which satisfies the iframe-exclusion rule
# for free.
DISCOVERY_SELECTOR = (
    "h1, h2, h3, h4, h5, h6, a, button, input, select, textarea, "
    "[role='button'], [role='menuitem'], [role='tab'], [role='link'], "
    "[role='checkbox'], [role='radio'], [role='switch'], [role='option']"
)

_MARKER_SCRIPT = """
(sel) => {
  const els = Array.from(document.querySelectorAll(sel));
  els.forEach((el, i) => el.setAttribute('data-ll-idx', String(i)));
  return els.length;
}
"""

logger = get_logger()


def validate_url(url: str) -> None:
    """Validate scheme/format before any network call is attempted."""
    if not url or not url.strip():
        raise InvalidUrlError("URL is empty. Provide a valid http/https URL.")
    parsed = urlparse(url.strip())
    if parsed.scheme not in ALLOWED_SCHEMES:
        raise InvalidUrlError(
            f"Unsupported URL scheme '{parsed.scheme or '(none)'}'. "
            "Only http:// and https:// are supported."
        )
    if not parsed.netloc:
        raise InvalidUrlError(
            "URL is missing a host. Provide a fully-qualified URL, e.g. " "https://example.com."
        )


def _count_redirects(response) -> int:
    """Walk the redirect chain via Playwright's ``redirected_from`` link."""
    count = 0
    request = response.request
    while request is not None and request.redirected_from is not None:
        count += 1
        request = request.redirected_from
    return count


def _make_route_handler(error_holder: dict):
    """Build the ``page.route()`` handler implementing Must-Do #2."""

    def handle_route(route) -> None:
        request = route.request
        if request.resource_type != "document":
            route.continue_()
            return
        try:
            response = route.fetch()
        except Exception as exc:  # pragma: no cover - network edge case
            error_holder["error"] = RenderError(f"Failed to fetch page: {exc}")
            route.abort()
            return

        content_length = response.headers.get("content-length")
        too_large = False
        if content_length is not None:
            try:
                too_large = int(content_length) > MAX_BYTES
            except ValueError:
                too_large = False

        if not too_large and content_length is None:
            body = response.body()
            too_large = len(body) > MAX_BYTES

        if too_large:
            mb = MAX_BYTES // (1024 * 1024)
            error_holder["error"] = PageTooLargeError(
                f"Page response exceeded the {mb}MB analysis limit. " "Try a smaller/simpler page."
            )
            route.abort()
            return

        route.fulfill(response=response)

    return handle_route


def acquire_url(page, url: str, timeout_ms: int = TIMEOUT_MS) -> PageSource:
    """Navigate ``page`` (a live Playwright Page) to ``url`` and return a
    marker-injected ``PageSource``. Raises typed exceptions on failure;
    callers should catch and fall back to raw fetch (Requirement 7)."""
    validate_url(url)
    error_holder: dict = {}
    page.route(lambda r: True, _make_route_handler(error_holder))

    try:
        response = page.goto(url, wait_until="networkidle", timeout=timeout_ms)
    except Exception as exc:
        if "error" in error_holder:
            raise error_holder["error"] from exc
        message = str(exc)
        if "Timeout" in message or "timeout" in message:
            raise FetchTimeoutError(
                "Page took >30s to load. Try a simpler page or check network."
            ) from exc
        if any(t in message for t in ("SSL", "CERT", "certificate")):
            raise TlsValidationError(
                "TLS certificate validation failed for this URL. The site's "
                "certificate may be invalid, self-signed, or expired."
            ) from exc
        raise RenderError(f"Failed to render page: {message}") from exc

    if "error" in error_holder:
        raise error_holder["error"]

    if response is not None and _count_redirects(response) > MAX_REDIRECTS:
        raise TooManyRedirectsError(
            f"URL redirected more than {MAX_REDIRECTS} times. " "This may indicate a redirect loop."
        )

    page.evaluate(_MARKER_SCRIPT, DISCOVERY_SELECTOR)
    html = page.content()
    return PageSource(html=html, mode="url", source_label=url, rendered=True, page=page)


def fetch_raw_fallback(url: str, timeout_s: float = 30.0) -> PageSource:
    """Fetch ``url`` as plain HTTP (no JS render) — Playwright fallback path
    used when rendering fails (Requirement 7 graceful degradation)."""
    try:
        with httpx.Client(
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            timeout=timeout_s,
            verify=True,
        ) as client:
            resp = client.get(url)
    except httpx.TooManyRedirects as exc:
        raise TooManyRedirectsError(f"URL redirected more than {MAX_REDIRECTS} times.") from exc
    except httpx.TimeoutException as exc:
        raise FetchTimeoutError(
            "Page took >30s to load. Try a simpler page or check network."
        ) from exc
    except httpx.ConnectError as exc:
        if "certificate" in str(exc).lower() or "SSL" in str(exc):
            raise TlsValidationError("TLS certificate validation failed for this URL.") from exc
        raise InvalidUrlError(f"Could not connect to host: {exc}") from exc

    if len(resp.content) > MAX_BYTES:
        mb = MAX_BYTES // (1024 * 1024)
        raise PageTooLargeError(
            f"Page response exceeded the {mb}MB analysis limit. " "Try a smaller/simpler page."
        )

    html = decode_raw_html(resp.content)
    return PageSource(
        html=html,
        mode="url",
        source_label=url,
        rendered=False,
        degraded=True,
        degradation_reason="JavaScript rendering failed; analyzed static HTML instead.",
    )


def decode_raw_html(data: bytes) -> str:
    """Strict UTF-8 decode; only truly unparseable content is rejected."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise UnparseableContentError(
            "Content could not be decoded as UTF-8 text. Binary or "
            "non-UTF8 content is not supported."
        ) from exc


def acquire_raw_html(data: bytes, source_label: str = "Raw HTML") -> PageSource:
    """Validate size, decode, and wrap raw HTML/upload input."""
    if len(data) > MAX_BYTES:
        mb = MAX_BYTES // (1024 * 1024)
        raise PageTooLargeError(
            f"Submitted HTML exceeded the {mb}MB analysis limit. " "Try a smaller document."
        )
    html = decode_raw_html(data)
    return PageSource(html=html, mode="raw_html", source_label=source_label, rendered=False)
