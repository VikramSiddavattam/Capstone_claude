"""FastAPI route definitions (design-document Component 2).

Routes are declared as plain (sync) ``def`` functions rather than
``async def``. Starlette runs sync route handlers in a worker thread pool
automatically, which lets this layer call Playwright's *synchronous* API
directly instead of bridging to `asyncio` per request — a small, documented
deviation from the design document's "async-first" rationale, made because
the sync Playwright API is materially simpler to reason about for a
single-lock, single-analysis-at-a-time pipeline (see
`documents/implementation-summary.md`).
"""

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from app.exceptions import LocatorLensError
from app.logging_config import get_logger
from app.pipeline import pipeline, report

router = APIRouter()
logger = get_logger()

VALID_MODES = {"url", "raw_html"}


@router.get("/", response_class=HTMLResponse)
def get_form() -> HTMLResponse:
    return HTMLResponse(report.render_form())


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _read_raw_html_input(
    html_text: Optional[str], html_file: Optional[UploadFile]
) -> tuple[Optional[bytes], str]:
    if html_file is not None and html_file.filename:
        return html_file.file.read(), html_file.filename
    if html_text and html_text.strip():
        return html_text.encode("utf-8"), "Raw HTML"
    return None, "Raw HTML"


@router.post("/analyze", response_class=HTMLResponse)
def analyze(
    mode: str = Form(...),
    url: Optional[str] = Form(None),
    html_text: Optional[str] = Form(None),
    html_file: Optional[UploadFile] = File(None),
) -> HTMLResponse:
    if mode not in VALID_MODES:
        body = report.render_error(f"Invalid mode '{mode}'. Must be 'url' or 'raw_html'.", 422)
        return HTMLResponse(body, status_code=422)

    if not pipeline.ANALYSIS_LOCK.acquire(blocking=False):
        body = report.render_error(
            "Another analysis is already in progress (single-analysis-at-a-time "
            "MVP). Please wait a moment and try again.",
            429,
        )
        return HTMLResponse(body, status_code=429)

    start = time.time()
    logger.info("Analyze request started: mode=%s", mode)
    try:
        if mode == "url":
            if not url or not url.strip():
                body = report.render_error("URL is required for URL mode.", 400)
                return HTMLResponse(body, status_code=400)
            html = pipeline.analyze_url(url.strip())
        else:
            data, label = _read_raw_html_input(html_text, html_file)
            if not data:
                body = report.render_error(
                    "Provide HTML text or upload a file for raw HTML mode.", 400
                )
                return HTMLResponse(body, status_code=400)
            html = pipeline.analyze_raw_html(data, label)

        logger.info("Analyze request completed in %.2fs", time.time() - start)
        return HTMLResponse(html)

    except LocatorLensError as exc:
        logger.warning("Analysis failed (%s): %s", type(exc).__name__, exc.message)
        return HTMLResponse(report.render_error(exc.message, 400), status_code=400)

    except Exception:  # pragma: no cover - unexpected/defensive path
        logger.exception("Unexpected error during analysis")
        body = report.render_error(
            "An unexpected error occurred while analyzing this page. "
            "Please try again or contact support if it persists.",
            500,
        )
        return HTMLResponse(body, status_code=500)

    finally:
        pipeline.ANALYSIS_LOCK.release()
