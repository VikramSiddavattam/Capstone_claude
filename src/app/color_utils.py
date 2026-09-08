"""Color normalization utility shared by the rendered and raw-HTML style
extraction paths (design-document Component 6).

Converts ``rgb()``/``rgba()`` functional notation and a small set of common
CSS named colors into ``#RRGGBB`` hex. Anything it cannot confidently
resolve returns ``None`` so callers can fall back to "Not Available" rather
than guessing (Requirement 5/8).
"""

from __future__ import annotations

import re
from typing import Optional

_RGB_RE = re.compile(
    r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*[\d.]+\s*)?\)",
    re.IGNORECASE,
)
_HEX3_RE = re.compile(r"^#([0-9a-fA-F]{3})$")
_HEX6_RE = re.compile(r"^#([0-9a-fA-F]{6})$")

# Small, common subset; not exhaustive by design (rule-based MVP, per
# requirements' "no AI/ML optimization" out-of-scope note).
_NAMED_COLORS = {
    "black": "#000000",
    "white": "#ffffff",
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "gray": "#808080",
    "grey": "#808080",
    "yellow": "#ffff00",
    "orange": "#ffa500",
    "purple": "#800080",
    "silver": "#c0c0c0",
    "transparent": None,  # cannot resolve to a color; caller treats as N/A
}


def to_hex(value: Optional[str]) -> Optional[str]:
    """Normalize a CSS color value to lowercase ``#rrggbb`` hex, or None."""
    if not value:
        return None
    value = value.strip()

    hex6 = _HEX6_RE.match(value)
    if hex6:
        return f"#{hex6.group(1).lower()}"

    hex3 = _HEX3_RE.match(value)
    if hex3:
        r, g, b = hex3.group(1)
        return f"#{r}{r}{g}{g}{b}{b}".lower()

    rgb = _RGB_RE.match(value)
    if rgb:
        r, g, b = (int(c) for c in rgb.groups())
        if all(0 <= c <= 255 for c in (r, g, b)):
            return f"#{r:02x}{g:02x}{b:02x}"
        return None

    named = _NAMED_COLORS.get(value.lower())
    return named
