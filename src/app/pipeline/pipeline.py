"""Analysis Pipeline orchestrator — wires Components 3-7 together.

Per-element failures (XPath/style extraction) are caught and recorded as
"Failed" report rows rather than aborting the whole analysis (Requirement 6
partial-failure handling). Fatal, page-level failures (invalid URL, timeout,
TLS, unparseable content, no elements found, oversized page) propagate as
typed exceptions for the FastAPI route layer to map to an error response.
"""

from __future__ import annotations

import threading
from typing import Optional

from playwright.sync_api import sync_playwright

from app.exceptions import RenderError
from app.logging_config import get_logger
from app.models import NOT_AVAILABLE, PageSource
from app.pipeline import (discovery, input_acquisition, report, style_extract,
                          xpath_gen)

# Single-analysis lock (Requirement 9 — single-threaded MVP). Acquired by
# the FastAPI route layer around a full analysis; released unconditionally.
ANALYSIS_LOCK = threading.Lock()

logger = get_logger()


def _build_rows(soup, elements, page_source: PageSource):
    css_rules = None if page_source.rendered else style_extract.parse_css_rules(soup)
    rows = []
    for element in elements:
        try:
            xpath_result = xpath_gen.generate_xpath(element, soup)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("XPath generation failed for element")
            rows.append(
                report.build_element_report(
                    element,
                    "N/A",
                    True,
                    NOT_AVAILABLE,
                    NOT_AVAILABLE,
                    NOT_AVAILABLE,
                    status="Failed",
                    reason=f"XPath generation failed: {exc}",
                )
            )
            continue

        try:
            style_result = style_extract.extract_style(element, page_source, css_rules)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Style extraction failed for element")
            rows.append(
                report.build_element_report(
                    element,
                    xpath_result.xpath,
                    xpath_result.fragile,
                    NOT_AVAILABLE,
                    NOT_AVAILABLE,
                    NOT_AVAILABLE,
                    status="Failed",
                    reason=f"Style extraction failed: {exc}",
                )
            )
            continue

        rows.append(
            report.build_element_report(
                element,
                xpath_result.xpath,
                xpath_result.fragile,
                style_result.font_family,
                style_result.font_size,
                style_result.font_color,
            )
        )
    return rows


def _render_for_source(page_source: PageSource) -> str:
    soup, elements = discovery.discover_elements(page_source)
    rows = _build_rows(soup, elements, page_source)
    metadata = report.build_metadata(soup, page_source, elements)
    return report.render_report(metadata, rows)


def analyze_url(url: str) -> str:
    """Run the full analysis pipeline for URL-mode input."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            context = browser.new_context()
            page = context.new_page()
            try:
                page_source = input_acquisition.acquire_url(page, url)
            except RenderError as exc:
                logger.warning("Render failed for %s, falling back: %s", url, exc)
                page_source = input_acquisition.fetch_raw_fallback(url)
            return _render_for_source(page_source)
        finally:
            browser.close()


def analyze_raw_html(data: bytes, source_label: Optional[str] = None) -> str:
    """Run the full analysis pipeline for raw-HTML/upload-mode input."""
    page_source = input_acquisition.acquire_raw_html(data, source_label or "Raw HTML")
    return _render_for_source(page_source)
