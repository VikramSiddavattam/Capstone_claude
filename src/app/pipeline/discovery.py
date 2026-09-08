"""DOM Parsing & Element Discovery Module (design-document Component 4).

Parses the normalized ``PageSource.html`` with BeautifulSoup/lxml and
discovers the 8 target element types, applying the hidden/iframe/viewport
exclusion rules from Requirement 3.

Node correlation (impl-plan Must-Do #1): in rendered mode, ``PageSource.html``
is the *post-marker-injection* snapshot captured by
``input_acquisition.acquire_url``, so every candidate BS4 node already
carries a ``data-ll-idx`` attribute that matches the live Playwright DOM.
``DiscoveredElement.node_key`` is that value (rendered mode) or a stable
pre-order positional index (raw-HTML mode, no live DOM to correlate with).
"""

from __future__ import annotations

from typing import List, Optional

from bs4 import BeautifulSoup, Tag

from app.exceptions import NoElementsFoundError, UnparseableContentError
from app.models import DiscoveredElement, PageSource

CLICKABLE_ROLES = {
    "button",
    "menuitem",
    "tab",
    "link",
    "checkbox",
    "radio",
    "switch",
    "option",
}

DISCOVERY_SELECTOR = (
    "h1, h2, h3, h4, h5, h6, a, button, input, select, textarea, "
    "[role='button'], [role='menuitem'], [role='tab'], [role='link'], "
    "[role='checkbox'], [role='radio'], [role='switch'], [role='option']"
)


def classify_element(tag_name: str, attrs: dict) -> Optional[str]:
    """Map a tag+attrs combination to one of the 8 element types, using a
    fixed priority so a single element is never double-classified."""
    tag_name = tag_name.lower()
    role = (attrs.get("role") or "").lower()
    type_attr = (attrs.get("type") or "").lower()

    if tag_name == "h1":
        return "heading"
    if tag_name in {"h2", "h3", "h4", "h5", "h6"}:
        return "subheading"
    if tag_name == "a":
        return "link"
    if tag_name == "button" or (tag_name == "input" and type_attr == "button"):
        return "button"
    if tag_name == "input":
        return "input"
    if tag_name == "select":
        return "dropdown"
    if tag_name == "textarea":
        return "textarea"
    if role in CLICKABLE_ROLES:
        return "clickable_role"
    return None


def _has_iframe_ancestor(tag: Tag) -> bool:
    parent = tag.parent
    while parent is not None:
        if getattr(parent, "name", None) == "iframe":
            return True
        parent = parent.parent
    return False


def _has_hidden_aria_ancestor(tag: Tag) -> bool:
    """aria-hidden is not reflected in Playwright's is_visible()/bounding
    box, so it must be checked explicitly (self + ancestors) in both
    rendered and raw-HTML modes."""
    node: Optional[Tag] = tag
    while node is not None and getattr(node, "name", None) is not None:
        if (node.get("aria-hidden") or "").lower() == "true":
            return True
        node = node.parent
    return False


def _is_hidden_self(tag: Tag) -> bool:
    if (tag.get("aria-hidden") or "").lower() == "true":
        return True
    if tag.get("hidden") is not None:
        return True
    style = (tag.get("style") or "").lower().replace(" ", "")
    if "display:none" in style or "visibility:hidden" in style:
        return True
    return False


def _is_hidden_static(tag: Tag) -> bool:
    """Best-effort hidden check for non-rendered (raw HTML) input, using
    inline style/attributes only (no CSS cascade resolution available).
    Inheritance is approximated by walking ancestors: a hidden ancestor
    (e.g. display:none on a wrapping <div>) hides all its descendants,
    even though this element's own attributes look visible."""
    node: Optional[Tag] = tag
    while node is not None and getattr(node, "name", None) is not None:
        if _is_hidden_self(node):
            return True
        node = node.parent
    return False


def resolve_live_handle(page, node_key: str):
    """Return the Playwright Locator correlated with ``node_key`` — the
    core of the Must-Do #1 correlation mechanism (O(1) attribute lookup,
    never a positional re-scan or re-derived XPath)."""
    return page.locator(f'[data-ll-idx="{node_key}"]')


def _is_hidden_rendered(page, node_key: str) -> bool:
    """Visibility + viewport-intersection check using the live handle."""
    locator = resolve_live_handle(page, node_key)
    try:
        if locator.count() == 0 or not locator.first.is_visible():
            return True
        bbox = locator.first.bounding_box()
        if bbox is None:
            return True
        viewport = page.viewport_size
        if viewport and (
            bbox["x"] + bbox["width"] <= 0
            or bbox["y"] + bbox["height"] <= 0
            or bbox["x"] >= viewport["width"]
            or bbox["y"] >= viewport["height"]
        ):
            return True
        return False
    except Exception:  # pragma: no cover - defensive fail-safe
        return True


def _parse_html(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception as exc:  # pragma: no cover - lxml is highly tolerant
        raise UnparseableContentError(f"Could not parse HTML content: {exc}") from exc


def discover_elements(page_source: PageSource):
    """Discover all in-scope elements, excluding hidden/iframe/off-viewport
    nodes, raising ``NoElementsFoundError`` if nothing qualifies.

    Returns ``(soup, elements)`` — the parsed document is returned alongside
    the element list so downstream stages (XPath uniqueness checks, style
    cascade, metadata detection) can reuse the same tree without re-parsing.
    """
    soup = _parse_html(page_source.html)
    candidates = soup.select(DISCOVERY_SELECTOR)

    elements: List[DiscoveredElement] = []
    for idx, tag in enumerate(candidates):
        if _has_iframe_ancestor(tag):
            continue
        element_type = classify_element(tag.name, tag.attrs)
        if element_type is None:
            continue
        if _has_hidden_aria_ancestor(tag):
            continue

        if page_source.rendered and page_source.page is not None:
            node_key = tag.get("data-ll-idx")
            if node_key is None or _is_hidden_rendered(page_source.page, node_key):
                continue
        else:
            node_key = str(idx)
            if _is_hidden_static(tag):
                continue

        text = tag.get_text(strip=True)
        elements.append(
            DiscoveredElement(
                tag=tag.name,
                attrs=dict(tag.attrs),
                text=text,
                node_key=node_key,
                element_type=element_type,
                soup_node=tag,
            )
        )

    if not elements:
        raise NoElementsFoundError(
            "No matching elements were found on this page. It may be "
            "iframe-only, rendered entirely by client-side JavaScript after "
            "load, or contain none of the 8 supported element types."
        )
    return soup, elements
