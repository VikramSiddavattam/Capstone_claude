"""Metadata auto-detection helpers for the report header (Component 7):
Application Name and Frontend Technology. Both are explicitly best-effort
and heuristic — Requirement 8 permits (and this module relies on) falling
back to "Not Available" rather than guessing.
"""

from __future__ import annotations

from urllib.parse import urlparse

from app.models import NOT_AVAILABLE

_FRAMEWORK_SIGNATURES = (
    ("__NEXT_DATA__", "Next.js"),
    ("ng-version", "Angular"),
    ("data-reactroot", "React"),
    ("data-reactid", "React"),
    ("v-app", "Vue.js"),
    ('id="app" data-v-app', "Vue.js"),
)


def detect_app_name(soup, source_label: str, mode: str) -> str:
    title_tag = soup.find("title")
    if title_tag and title_tag.get_text(strip=True):
        return title_tag.get_text(strip=True)
    if mode == "url":
        host = urlparse(source_label).netloc
        if host:
            return host
    return NOT_AVAILABLE


def detect_frontend_technology(soup, html: str) -> str:
    generator = soup.find("meta", attrs={"name": "generator"})
    if generator and generator.get("content"):
        return generator["content"].strip()

    for signature, name in _FRAMEWORK_SIGNATURES:
        if signature in html:
            return name

    for script in soup.find_all("script", src=True):
        src = script["src"].lower()
        if "react" in src:
            return "React"
        if "vue" in src:
            return "Vue.js"
        if "angular" in src:
            return "Angular"

    return NOT_AVAILABLE
