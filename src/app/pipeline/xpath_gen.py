"""XPath Generation Module (design-document Component 5).

Pure rule-based generation, priority order per Requirement 4:
  1. ID-based, if unique in the document.
  2. Unique ``name`` / ``data-testid`` / ``aria-label``.
  3. Shortest robust relative XPath (tag + normalized text, else
     tag + sibling position), tagged ``fragile=True`` when it is the
     best-effort fallback (Requirement 8).

Every generated XPath is round-tripped through ``lxml.etree.XPath()``
before being returned, guaranteeing syntactic validity (AC4).
"""

from __future__ import annotations

from bs4 import Tag
from lxml import etree

from app.models import DiscoveredElement, XPathResult

_UNIQUE_ATTRS = ("name", "data-testid", "aria-label")
_MAX_TEXT_LEN = 60


def _xpath_literal(value: str) -> str:
    """Build a syntactically-safe XPath string literal for ``value``,
    handling embedded single/double quotes via ``concat()`` when needed."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    parts = value.split("'")
    return "concat(" + ', "\'", '.join(f"'{p}'" for p in parts) + ")"


def _validate(xpath: str) -> bool:
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def _is_unique_id(soup, id_value: str) -> bool:
    return len(soup.find_all(id=id_value)) == 1


def _is_unique_attr(soup, attr: str, value: str) -> bool:
    return len(soup.find_all(attrs={attr: value})) == 1


def _text_based_xpath(soup, tag: Tag, text: str) -> XPathResult | None:
    if not text or len(text) > _MAX_TEXT_LEN:
        return None
    matches = [t for t in soup.find_all(tag.name) if t.get_text(strip=True) == text]
    if len(matches) != 1:
        return None
    xpath = f"//{tag.name}[normalize-space(text())={_xpath_literal(text)}]"
    if not _validate(xpath):
        return None
    return XPathResult(xpath=xpath, fragile=False, strategy="text-based")


def _position_fallback_xpath(tag: Tag) -> XPathResult:
    parent = tag.parent
    siblings = parent.find_all(tag.name, recursive=False) if parent else [tag]
    try:
        position = siblings.index(tag) + 1
    except ValueError:  # pragma: no cover - defensive
        position = 1
    xpath = f"//{tag.name}[{position}]"
    if not _validate(xpath):
        xpath = f"//{tag.name}"  # last-resort, always syntactically valid
    return XPathResult(xpath=xpath, fragile=True, strategy="position-fallback")


def generate_xpath(element: DiscoveredElement, soup) -> XPathResult:
    """Compute the best-available XPath for ``element`` within ``soup``
    (the full parsed document, used for uniqueness checks)."""
    tag = element.soup_node

    id_value = tag.get("id")
    if id_value and _is_unique_id(soup, id_value):
        xpath = f"//*[@id={_xpath_literal(id_value)}]"
        if _validate(xpath):
            return XPathResult(xpath=xpath, fragile=False, strategy="id")

    for attr in _UNIQUE_ATTRS:
        value = tag.get(attr)
        if value and _is_unique_attr(soup, attr, value):
            xpath = f"//{tag.name}[@{attr}={_xpath_literal(value)}]"
            if _validate(xpath):
                return XPathResult(xpath=xpath, fragile=False, strategy="unique-attribute")

    text_result = _text_based_xpath(soup, tag, element.text.strip())
    if text_result is not None:
        return text_result

    return _position_fallback_xpath(tag)
