"""FastAPI application entry point.

Run locally with: ``uvicorn app.main:app --reload`` (from ``src/``).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.logging_config import configure_logging
from app.routes import router

configure_logging()

app = FastAPI(
    title="Locator Lens",
    description=(
        "Analyzes a webpage (URL or raw HTML), discovers UI elements, "
        "generates XPath locators, and extracts style metadata as an "
        "HTML report. Internal, local/dev-only QA tool."
    ),
    version="0.1.0",
)
app.include_router(router)
