"""Report Assembly & Rendering Module (design-document Component 7).

Combines discovery + XPath + style results with page-level metadata into
the final HTML report via Jinja2. Autoescaping is left at Jinja2's default
(on) so any HTML/script content reflected from the *analyzed* page is
safely escaped in the *report* page (Security Design, threat: reflected
XSS via analyzed page content).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.models import (DiscoveredElement, ElementReport, PageSource,
                        ReportMetadata)
from app.pipeline import tech_detect

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)

_RELEVANT_ATTR_KEYS = {"id", "name", "class"}


def _relevant_attributes(attrs: dict) -> dict:
    """Strip the synthetic ``data-ll-idx`` marker and keep only the
    attributes the report is required to surface (impl-plan §2.1 step 5)."""
    result = {}
    for key, value in attrs.items():
        if key == "data-ll-idx":
            continue
        if key in _RELEVANT_ATTR_KEYS or key.startswith("data-") or key.startswith("aria-"):
            result[key] = value
    return result


def _element_name(element: DiscoveredElement) -> str:
    text = element.text.strip()
    if text:
        return text[:80] + ("…" if len(text) > 80 else "")
    return element.attrs.get("id") or element.attrs.get("name") or f"<{element.tag}>"


def build_metadata(
    soup, page_source: PageSource, elements: List[DiscoveredElement]
) -> ReportMetadata:
    counts: dict = {}
    for element in elements:
        counts[element.element_type] = counts.get(element.element_type, 0) + 1

    app_name = tech_detect.detect_app_name(soup, page_source.source_label, page_source.mode)
    frontend_technology = tech_detect.detect_frontend_technology(soup, page_source.html)
    page_label = page_source.source_label if page_source.mode == "url" else "Raw HTML"

    return ReportMetadata(
        app_name=app_name,
        frontend_technology=frontend_technology,
        analysis_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        page_source_label=page_label,
        total_elements=len(elements),
        counts_by_type=counts,
        degraded=page_source.degraded,
        degradation_reason=page_source.degradation_reason,
    )


def build_element_report(
    element: DiscoveredElement,
    xpath: str,
    fragile: bool,
    font_family: str,
    font_size: str,
    font_color: str,
    status: str = "OK",
    reason: Optional[str] = None,
) -> ElementReport:
    return ElementReport(
        name=_element_name(element),
        element_type=element.element_type,
        tag=element.tag,
        xpath=xpath,
        fragile=fragile,
        font_family=font_family,
        font_size=font_size,
        font_color=font_color,
        attributes=_relevant_attributes(element.attrs),
        status=status,
        reason=reason,
    )


def render_report(metadata: ReportMetadata, rows: List[ElementReport]) -> str:
    template = _env.get_template("report.html")
    return template.render(metadata=metadata, rows=rows)


def render_error(message: str, status_code: int) -> str:
    template = _env.get_template("error.html")
    return template.render(message=message, status_code=status_code)


def render_form() -> str:
    template = _env.get_template("form.html")
    return template.render()
