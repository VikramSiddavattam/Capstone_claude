"""Plain data models shared across pipeline stages.

Dataclasses (not Pydantic) are used here deliberately: these objects flow
through in-process pipeline code only (never (de)serialized over a network
boundary), and some carry references to non-serializable objects (e.g. a
BeautifulSoup ``Tag``). Pydantic models are reserved for the FastAPI request
boundary (see ``app.routes``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

NOT_AVAILABLE = "Not Available"


@dataclass
class PageSource:
    """Normalized input produced by the Input Acquisition module."""

    html: str
    mode: str  # "url" | "raw_html"
    source_label: str
    rendered: bool
    degraded: bool = False
    degradation_reason: Optional[str] = None
    page: Optional[Any] = None  # live playwright.sync_api.Page, url mode only


@dataclass
class DiscoveredElement:
    """A single UI element discovered during DOM parsing (Component 4)."""

    tag: str
    attrs: dict
    text: str
    node_key: str
    element_type: str
    soup_node: Any = None  # bs4.Tag, used by XPath/style stages


@dataclass
class XPathResult:
    """Output of Component 5 for a single element."""

    xpath: str
    fragile: bool
    strategy: str


@dataclass
class StyleResult:
    """Output of Component 6 for a single element."""

    font_family: str = NOT_AVAILABLE
    font_size: str = NOT_AVAILABLE
    font_color: str = NOT_AVAILABLE
    visible_text: str = ""


@dataclass
class ElementReport:
    """A fully assembled row for the Element Analysis Table (Component 7)."""

    name: str
    element_type: str
    tag: str
    xpath: str
    fragile: bool
    font_family: str
    font_size: str
    font_color: str
    attributes: dict
    status: str = "OK"  # "OK" | "Failed" | "Skipped"
    reason: Optional[str] = None


@dataclass
class ReportMetadata:
    """Page-level metadata header for the report (Component 7)."""

    app_name: str
    frontend_technology: str
    analysis_timestamp: str
    page_source_label: str
    total_elements: int
    counts_by_type: dict = field(default_factory=dict)
    degraded: bool = False
    degradation_reason: Optional[str] = None
