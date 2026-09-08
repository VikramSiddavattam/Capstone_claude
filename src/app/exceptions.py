"""Typed exception hierarchy for Locator Lens (design-document Component 8).

Each exception carries a human-actionable `message` so the FastAPI route
layer can render it directly in the report-shell error template without
needing to re-derive user-facing copy from an exception class name.
"""

from __future__ import annotations


class LocatorLensError(Exception):
    """Base class for all Locator Lens domain errors."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidUrlError(LocatorLensError):
    """Raised when a submitted URL fails scheme/format validation."""


class FetchTimeoutError(LocatorLensError):
    """Raised when the combined fetch+render exceeds the 30s budget."""


class TlsValidationError(LocatorLensError):
    """Raised when TLS certificate validation fails for a target URL."""


class UnparseableContentError(LocatorLensError):
    """Raised when input HTML/binary content cannot be decoded/parsed."""


class NoElementsFoundError(LocatorLensError):
    """Raised when the discovery stage finds zero matching elements."""


class PageTooLargeError(LocatorLensError):
    """Raised when a fetched/uploaded page exceeds the ~5MB size cap."""


class TooManyRedirectsError(LocatorLensError):
    """Raised when a navigation exceeds the 5-redirect cap."""


class RenderError(LocatorLensError):
    """Raised when Playwright rendering fails outright (pre-fallback)."""
