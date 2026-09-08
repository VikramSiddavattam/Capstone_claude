"""Style Metadata Extraction Module (design-document Component 6).

Rendered mode: true browser-engine ``getComputedStyle`` via the live
Playwright handle resolved through the Must-Do #1 correlation utility
(``discovery.resolve_live_handle``) — cascade/inheritance are resolved by
Chromium itself.

Raw-HTML mode: a deliberately simple ``tinycss2``-based approximation that
only resolves *simple* selectors (tag, ``.class``, ``#id`` — no
combinators, pseudo-classes, or attribute selectors). Anything it cannot
confidently resolve is reported as "Not Available" rather than guessed,
per Requirement 5/8 and the design document's own documented limitation.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import tinycss2
from bs4 import Tag

from app.color_utils import to_hex
from app.models import (NOT_AVAILABLE, DiscoveredElement, PageSource,
                        StyleResult)
from app.pipeline.discovery import resolve_live_handle

CssRule = Tuple[str, dict, Tuple[int, int, int]]

_COMPUTED_STYLE_JS = """
el => {
  const s = getComputedStyle(el);
  return { fontFamily: s.fontFamily, fontSize: s.fontSize, color: s.color };
}
"""


def _simple_specificity(selector: str) -> Optional[Tuple[int, int, int]]:
    """Return a specificity tuple for *simple* selectors only; None marks
    the selector as unsupported (compound/combinator/pseudo), causing the
    caller to skip it rather than risk an incorrect match."""
    if not selector or any(c in selector for c in " >~+:[*"):
        return None
    if selector.startswith("#"):
        return (1, 0, 0)
    if selector.startswith("."):
        return (0, 1, 0)
    if selector.isidentifier() or selector.isalpha():
        return (0, 0, 1)
    return None


def _parse_declaration_tokens(tokens) -> dict:
    declarations = {}
    for decl in tinycss2.parse_declaration_list(tokens, skip_whitespace=True, skip_comments=True):
        if decl.type == "declaration":
            value = tinycss2.serialize(decl.value).strip()
            declarations[decl.lower_name] = value
    return declarations


def parse_css_rules(soup) -> List[CssRule]:
    """Extract simple-selector rules from every ``<style>`` block in the
    document, used by the raw-HTML cascade approximation."""
    rules: List[CssRule] = []
    for style_tag in soup.find_all("style"):
        css_text = style_tag.get_text()
        stylesheet = tinycss2.parse_stylesheet(css_text, skip_whitespace=True, skip_comments=True)
        for rule in stylesheet:
            if rule.type != "qualified-rule":
                continue
            selectors_text = tinycss2.serialize(rule.prelude).strip()
            declarations = _parse_declaration_tokens(rule.content)
            for raw_selector in selectors_text.split(","):
                selector = raw_selector.strip()
                specificity = _simple_specificity(selector)
                if specificity is not None and declarations:
                    rules.append((selector, declarations, specificity))
    return rules


def _selector_matches(selector: str, tag: Tag) -> bool:
    if selector.startswith("#"):
        return tag.get("id") == selector[1:]
    if selector.startswith("."):
        return selector[1:] in (tag.get("class") or [])
    return tag.name == selector


def _resolve_raw_declarations(tag: Tag, rules: List[CssRule]) -> dict:
    matched = sorted(
        (rule for rule in rules if _selector_matches(rule[0], tag)),
        key=lambda rule: rule[2],
    )
    resolved: dict = {}
    for _, declarations, _ in matched:
        resolved.update(declarations)  # higher specificity applied last

    inline_style = tag.get("style")
    if inline_style:
        resolved.update(_parse_declaration_tokens(inline_style))
    return resolved


def _extract_style_raw(element: DiscoveredElement, rules: List[CssRule]) -> StyleResult:
    resolved = _resolve_raw_declarations(element.soup_node, rules)
    font_family = resolved.get("font-family") or NOT_AVAILABLE
    font_size = resolved.get("font-size") or NOT_AVAILABLE
    color_hex = to_hex(resolved.get("color")) if resolved.get("color") else None
    return StyleResult(
        font_family=font_family,
        font_size=font_size,
        font_color=color_hex or NOT_AVAILABLE,
        visible_text=element.text,
    )


def _extract_style_rendered(element: DiscoveredElement, page) -> StyleResult:
    try:
        locator = resolve_live_handle(page, element.node_key)
        data = locator.first.evaluate(_COMPUTED_STYLE_JS)
    except Exception:  # pragma: no cover - defensive: element detached, etc.
        return StyleResult(visible_text=element.text)

    color_hex = to_hex(data.get("color")) if data.get("color") else None
    return StyleResult(
        font_family=data.get("fontFamily") or NOT_AVAILABLE,
        font_size=data.get("fontSize") or NOT_AVAILABLE,
        font_color=color_hex or NOT_AVAILABLE,
        visible_text=element.text,
    )


def extract_style(
    element: DiscoveredElement,
    page_source: PageSource,
    css_rules: Optional[List[CssRule]] = None,
) -> StyleResult:
    """Resolve font family/size/color for ``element``. Requirement 5 scopes
    this to elements with visible text; elements without text return all
    "Not Available" style fields plus an empty ``visible_text``."""
    if not element.text.strip():
        return StyleResult(visible_text="")

    if page_source.rendered and page_source.page is not None:
        return _extract_style_rendered(element, page_source.page)

    return _extract_style_raw(element, css_rules or [])
