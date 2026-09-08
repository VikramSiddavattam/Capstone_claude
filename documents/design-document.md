# System Architecture Design: Locator Lens

**Story ID**: EPMCDMETST-62704
**Phase**: 2 — Solution Architecture
**Date**: 2026-08-31
**Status**: Draft — Pending design-reviewer approval
**Input**: `documents/requirements.md` (Approved 2026-08-31)

---

## Overview

Locator Lens is a single-process, stateless, local/dev-only web application that
analyzes a webpage (via URL or raw HTML), discovers UI elements of 8 defined
types, generates prioritized XPath locators, extracts computed style metadata,
and renders the results as a self-contained HTML report directly in the user's
browser.

The architecture is intentionally simple, reflecting the requirements' explicit
constraints: no authentication, no database, no concurrency/queuing, no
external services, single-threaded MVP, local/dev deployment only. The design
favors a small number of cohesive, testable Python modules over a distributed
or service-oriented topology — there is no scaling, availability, or multi-user
concern to justify additional complexity.

Two already-locked technical decisions anchor every component below:
- **Backend**: Python + FastAPI, with Playwright (Chromium-only) for rendering
  and BeautifulSoup/lxml for HTML parsing.
- **Delivery**: The analysis report is returned as rendered HTML in the HTTP
  response body and displayed by the browser — never written to disk or offered
  as a download.

---

## System Components

### Component 1: Web UI / Entry Form
- **Purpose**: Single HTML page where the user submits a URL or pastes/uploads
  raw HTML.
- **Technology**: Server-rendered HTML (Jinja2 templates), minimal vanilla JS
  (form submit only — no SPA framework, per requirements' "lightweight web UI").
- **Responsibility**: Collect input, perform client-side basic validation (non-
  empty, scheme hint), submit to the `/analyze` endpoint via standard HTML
  POST (full-page navigation, not AJAX) so that the FastAPI response (the
  rendered report HTML) replaces the page directly — this satisfies "report
  displayed in browser, not downloaded" with zero extra client-side plumbing.
- **Interfaces**: HTTP POST to `POST /analyze` (form-encoded / multipart for
  file upload).

### Component 2: FastAPI Application Layer (API + Orchestration)
- **Purpose**: HTTP entry point; validates request shape, dispatches to the
  Analysis Pipeline, catches pipeline errors, and returns either the rendered
  report or an error page.
- **Technology**: FastAPI + Uvicorn (ASGI), Pydantic models for request
  validation.
- **Responsibility**:
  - Route definitions (`/`, `/analyze`, `/health`).
  - Request validation (input mode selection, size pre-check on raw HTML/
    upload body via `Content-Length` + streaming cap).
  - Single global analysis lock (or simple in-process mutex) enforcing
    "single analysis at a time" (Requirement 9 — single-threaded MVP).
  - Translating pipeline exceptions into the Error Handling contract
    (Requirement 7) and rendering the error via the same report template
    shell.
  - Structured logging of each request lifecycle (basic file/console logger).
- **Interfaces**: Exposes REST endpoints (see API Contracts). Calls into the
  Analysis Pipeline as a plain in-process function call — no network hop.

### Component 3: Input Acquisition Module
- **Purpose**: Turn user-supplied input (URL or raw HTML/file) into a single
  normalized "page source" (HTML string + rendering flag) ready for parsing.
- **Technology**: Python `urllib.parse` for URL validation; `httpx`/Playwright
  navigation for fetch; Playwright (Chromium) for JS rendering.
- **Responsibility**:
  - **URL path**: validate scheme (http/https only) and format; open a
    Playwright Chromium browser context; navigate with `wait_until="networkidle"`
    (best-effort, bounded); enforce TLS certificate validation (Playwright
    default — do not disable `ignore_https_errors`); enforce combined
    fetch+render timeout of 30s; enforce max 5 redirects (Chromium's default
    navigation redirect handling, explicitly checked/capped); enforce ~5MB
    response size ceiling (abort navigation / truncate check via
    `Response` content-length and streamed byte counting).
  - **Raw HTML path**: accept pasted text or uploaded file; enforce ~5MB size
    cap before parsing; decode as UTF-8, rejecting (with a clear error) only
    when decoding fails or content is binary/non-text.
  - On Playwright render failure, falls back to fetching and parsing the raw
    response body as static HTML (degrade gracefully — Requirement 7),
    flagging the degradation for the report footer.
  - Returns a `PageSource` value object: `{html: str, mode: "url"|"raw_html",
    source_label: str, rendered: bool, degraded: bool}`.
- **Interfaces**: Pure function/class called by the Orchestration layer;
  no external interfaces beyond Playwright's browser automation and outbound
  HTTP fetch to the target URL (only in URL mode).

### Component 4: DOM Parsing & Element Discovery Module
- **Purpose**: Parse the normalized HTML into a DOM tree and discover all
  elements matching the 8 target types, applying visibility/iframe exclusions.
- **Technology**: BeautifulSoup4 with `lxml` parser (tolerant parsing, per
  Requirement 2); for rendered pages, element visibility/computed styles are
  additionally cross-checked via Playwright's live DOM handles (see Component 5)
  rather than static CSS parsing alone.
- **Responsibility**:
  - Parse HTML tolerantly; recover from malformed markup; raise a distinct
    `UnparseableContentError` only for truly binary/non-UTF8 input.
  - Traverse the DOM (BeautifulSoup tree for structure/attributes; Playwright
    `page.locator()` queries for live visibility state when `rendered=True`)
    and collect nodes matching: `h1`; `h2`–`h6`; `a`; `button` and
    `input[type=button]`; all `input` types; `select`; `textarea`; and any
    element with `role` in the clickable-role set (`button`, `menuitem`,
    `tab`, `link`, `checkbox`, `radio`, `switch`, `option`).
  - Excludes: elements inside any `<iframe>` (same- or cross-domain — simply
    never descends into iframe content documents); elements with
    `display:none`, `visibility:hidden`, or `aria-hidden="true"` (computed,
    not just inline, when rendered; inline/style-attribute heuristic when
    static); elements outside the viewport, for rendered pages, via
    Playwright's `is_visible()` (bounding-box + viewport intersection check).
  - Produces a list of `DiscoveredElement` objects carrying: tag name,
    attributes dict, text content, a stable node handle/index for downstream
    XPath and style extraction, and element-type classification.
- **Interfaces**: Consumes `PageSource`; produces `List[DiscoveredElement]`;
  called synchronously by the Orchestration layer.

### Component 5: XPath Generation Module
- **Purpose**: Compute the best-available XPath for each `DiscoveredElement`
  using the approved priority order.
- **Technology**: Pure Python; no external library (rule-based, per
  "Advanced XPath generation" being out of scope).
- **Responsibility**:
  - Priority 1: `id` attribute present and unique in document → `//*[@id='...']`.
  - Priority 2: unique `name`, `data-testid`, or `aria-label` among siblings/
    document → `//tag[@attr='value']`.
  - Priority 3: shortest robust relative XPath combining tag name, normalized
    text content, and/or sibling position index (`//tag[normalize-space(text())='...']`
    or `//tag[position]` fallback).
  - When none of the above yields a reasonably unique/stable locator, emits a
    best-effort absolute-ish XPath and tags the result with
    `fragile=True` so the report can render the "** Fragile **" note
    (Requirement 8).
  - Validates every generated XPath is syntactically well-formed by round-
    tripping it through `lxml.etree.XPath()` construction before returning it,
    guaranteeing "syntactically valid and testable" (AC4).
- **Interfaces**: Pure function `generate_xpath(element, document_context) ->
  XPathResult`; called once per discovered element.

### Component 6: Style Metadata Extraction Module
- **Purpose**: Resolve final (cascade-applied) Font Family, Font Size, Font
  Color, and Visible Text for each element with visible text.
- **Technology**: For rendered pages — Playwright's
  `page.evaluate("el => getComputedStyle(el)")` per element (true computed
  styles, cascade/inheritance resolved by the browser engine itself). For raw
  HTML (no JS execution, no live browser paint) — a lightweight cascade
  approximation using `tinycss2`/`cssutils` to parse `<style>` blocks and
  inline `style` attributes, applying basic specificity rules; this is
  explicitly a best-effort approximation, not a full CSS engine.
  Color values are normalized to `#RRGGBB` hex via a small `rgb()`/named-color
  → hex conversion utility shared by both paths.
- **Responsibility**:
  - Given rendered mode: batch-call `getComputedStyle` per element inside the
    existing Playwright page context (no extra page loads).
  - Given raw-HTML mode: apply the approximate cascade resolver; if resolution
    is inconclusive (e.g., dynamic CSS variables it cannot resolve, complex
    selectors it does not support), mark that field "Not Available" rather
    than guessing (Requirement 5/8).
  - Always returns `"Not Available"` for any field that cannot be determined,
    never an empty string or null.
- **Interfaces**: `extract_style(element, page_source) -> StyleResult`; called
  once per discovered element with non-empty visible text.

### Component 7: Report Assembly & Rendering Module
- **Purpose**: Combine discovery + XPath + style results with page-level
  metadata into the final HTML report and render it via a Jinja2 template.
- **Technology**: Jinja2 (already a FastAPI/Starlette dependency), plain CSS
  (no JS framework) for print-friendly, readable styling.
- **Responsibility**:
  - Auto-detect Application Name (page `<title>`, else URL host, else "Not
    Available") and Frontend Technology (meta generator tags, common
    framework script/global signatures such as `__NEXT_DATA__`, `ng-version`,
    `data-reactroot`, `Vue`; else "Not Available").
  - Assemble the metadata header block (app name, tech, timestamp, page
    source label, element counts by type, degradation notice if the render
    fell back to raw HTML).
  - Render the Element Analysis Table with the 8 required columns per element,
    substituting "Not Available" consistently, and flagging any element that
    failed processing (caught per-element, not pipeline-fatal) as
    "Failed"/"Skipped" with a reason string.
  - Return the fully rendered HTML string to the FastAPI route, which returns
    it as an `HTMLResponse`.
- **Interfaces**: `render_report(page_source, elements, metadata) -> str`
  (HTML); consumed directly by the FastAPI response.

### Component 8: Error Handling & Logging (Cross-Cutting)
- **Purpose**: Uniform, actionable error surfaces and basic operational
  logging across all components.
- **Technology**: Python `logging` module (console + rotating file handler);
  a small custom exception hierarchy (`InvalidUrlError`, `FetchTimeoutError`,
  `TlsValidationError`, `UnparseableContentError`, `NoElementsFoundError`).
- **Responsibility**: Each component raises typed exceptions with a
  human-actionable message; the FastAPI layer maps exception type → HTTP
  status + rendered error page (reusing the report template shell so the UX
  is consistent). Logs request start/end, timing, exception stack traces, and
  degradation events (e.g., Playwright render fallback).
- **Interfaces**: Cross-cutting; imported by all other components.

---

## Architecture Diagrams

### 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                              User's Browser                          │
│   (Chrome / Firefox / Safari / Edge — desktop)                       │
│                                                                       │
│   ┌─────────────────┐        ┌──────────────────────────────────┐    │
│   │  Input Form Page │──POST──▶│   Rendered Report Page (HTML)   │    │
│   │  (GET  /)         │        │   (returned directly by /analyze)│    │
│   └─────────────────┘        └──────────────────────────────────┘    │
└──────────────────────────────┬────────────────────────────────────────┘
                                │ HTTP (localhost, dev)
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    FastAPI App (Uvicorn, single process/worker)        │
│                                                                         │
│   Routes: GET /   POST /analyze   GET /health   GET /docs              │
│   Cross-cutting: request logging, single-analysis lock, error mapper   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │ in-process function calls (no network hop)
                                 ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         Analysis Pipeline (sync, single-threaded)      │
│                                                                         │
│  ① Input Acquisition  →  ② DOM Parsing & Element Discovery             │
│         │                          │                                   │
│         │ (URL mode only)          ▼                                   │
│         ▼                 ③ XPath Generation (per element)             │
│  Playwright (Chromium)             │                                   │
│  → outbound fetch to               ▼                                   │
│    target URL             ④ Style Metadata Extraction (per element)   │
│                                     │                                   │
│                                     ▼                                   │
│                          ⑤ Report Assembly (Jinja2) → HTML string      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTMLResponse
                                 ▼
                     back to User's Browser (renders report)
```

### 2. Component Interaction (Sequence)

```
User          WebUI(FastAPI)     InputAcq        DOMParser        XPathGen       StyleExtract     ReportAssembler
 │  submit URL/HTML  │               │                │                │              │                 │
 │──────────────────▶│                │                │                │              │                 │
 │                   │ acquire()      │                │                │              │                 │
 │                   │───────────────▶│                │                │              │                 │
 │                   │                │ (URL: Playwright launches       │              │                 │
 │                   │                │  Chromium, navigates, ≤30s,     │              │                 │
 │                   │                │  ≤5 redirects, TLS-validated)   │              │                 │
 │                   │                │ (raw HTML: decode + size check) │              │                 │
 │                   │◀───PageSource──│                │                │              │                 │
 │                   │  parse_and_discover()            │                │              │                 │
 │                   │────────────────────────────────▶│                │              │                 │
 │                   │◀───────────List[DiscoveredElement]                │              │                 │
 │                   │  for each element:               │                │              │                 │
 │                   │  generate_xpath() ───────────────────────────────▶│              │                 │
 │                   │◀──────────────────────────────────────XPathResult─│              │                 │
 │                   │  extract_style() ─────────────────────────────────────────────▶│                 │
 │                   │◀───────────────────────────────────────────────────StyleResult──│                 │
 │                   │  render_report(all results) ──────────────────────────────────────────────────▶│
 │                   │◀───────────────────────────────────────────────────────────────────HTML string──│
 │◀────HTMLResponse──│                │                │                │              │                 │
```

### 3. Data Flow Diagram

```
[User Input]
   URL  ──────┐
              ├──▶ [Input Acquisition] ──▶ PageSource{html, mode, rendered, degraded}
   Raw HTML ──┘            │
                            │ (URL mode: Playwright/Chromium
                            │  navigation to target site;
                            │  TLS + redirect + timeout + size enforcement)
                            ▼
                 [DOM Parsing & Element Discovery]
                     BeautifulSoup/lxml tree
                     (+ Playwright live DOM if rendered)
                            │
                            ▼
                 List[DiscoveredElement]
                     (8 types, hidden/iframe/viewport excluded)
                            │
                 ┌──────────┴───────────┐
                 ▼                      ▼
        [XPath Generation]     [Style Metadata Extraction]
         (priority: id >        (getComputedStyle if rendered;
          unique attr >          CSS-cascade approximation if raw HTML;
          relative XPath)        "Not Available" when unresolved)
                 │                      │
                 └──────────┬───────────┘
                            ▼
                 [Report Assembly (Jinja2)]
                     + page metadata (app name, tech, timestamp,
                       source, element counts, degradation notice)
                            │
                            ▼
                 HTML Report ──▶ HTTP Response ──▶ Browser renders in place
```

### 4. Deployment Architecture Diagram

```
Developer / QA Engineer machine (local/dev only — no staging/prod tier)
┌─────────────────────────────────────────────────────────────┐
│  Python 3.11+ virtualenv                                    │
│    pip install -r requirements.txt                           │
│    playwright install chromium                               │
│                                                                │
│  Process: uvicorn app.main:app --host 127.0.0.1 --port 8000  │
│    ├── FastAPI app (single worker, single thread of control) │
│    ├── Playwright-managed Chromium (headed or headless,      │
│    │    launched on demand per analysis, closed after)       │
│    └── Local log file: logs/locator-lens.log                 │
│                                                                │
│  No database. No message queue. No external services.        │
│  No containerization required for MVP (optional Dockerfile    │
│  may be added later without architecture change).             │
└─────────────────────────────────────────────────────────────┘
                          ▲
                          │ HTTP (localhost)
                          │
                 Browser on same machine
```

### 5. Error Handling Flow Diagram

```
Any Component raises typed exception
   (InvalidUrlError | FetchTimeoutError | TlsValidationError |
    UnparseableContentError | NoElementsFoundError | Exception)
                    │
                    ▼
      FastAPI route-level exception handler
                    │
        ┌───────────┴────────────┐
        ▼                        ▼
  Known/typed error         Unexpected error
  → map to actionable       → log full detail server-side
    message + 4xx            → generic safe message + 500
        │                        │
        └───────────┬────────────┘
                     ▼
       Render via same report-shell template
                     ▼
           HTMLResponse back to browser
```

---

## Technology Stack & Choices

Summary table, followed by full rationale (with alternatives considered) for
each major decision. Choices already locked by the approved requirements
(Python, FastAPI/Flask, Playwright/Chromium, BeautifulSoup/lxml, web-UI
delivery) are justified here in terms of the specific selection made within
that locked space (e.g., FastAPI vs. Flask), not re-litigated at the
language/tool-family level.

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| Web Framework | FastAPI |
| ASGI Server | Uvicorn |
| Rendering Engine | Playwright (Python), Chromium channel only |
| HTML Parsing | BeautifulSoup4 + `lxml` parser |
| Templating | Jinja2 |
| CSS Cascade (raw-HTML mode) | `tinycss2` |
| Testing | pytest, pytest-asyncio, pytest-playwright, pytest-cov |
| Deployment | Local Uvicorn process (no containerization required for MVP) |

### Why Python 3.11+?

**Alternatives Considered:**
- Node.js/TypeScript with Playwright's native JS bindings — rejected: the
  requirements explicitly lock the backend to Python.
- Java/Selenium — rejected: heavier tooling, requirements specify
  Playwright + Python bindings.

**Advantages of Python:**
- Native, first-class Playwright Python bindings.
- Mature, batteries-included parsing ecosystem (BeautifulSoup, lxml).
- Fast to prototype an internal exploratory tool; large hiring/team pool.

**Disadvantages/Trade-offs:**
- Slower raw execution than compiled languages — irrelevant here given the
  bottleneck is network fetch/render time (Playwright/Chromium), not Python
  CPU cycles, and volume is a single analysis at a time.
- GIL limits true parallelism — acceptable since the requirements mandate
  single-threaded, single-analysis-at-a-time processing anyway.

**Team Experience:** Python is broadly familiar to QA/automation engineering
teams (the tool's own target users); low learning curve for future
maintainers who are often already Python-literate from test automation work.

**Final Decision:** Python 3.11+, per approved requirements constraint.

### Why FastAPI (over Flask)?

**Alternatives Considered:**
- **Flask** — explicitly permitted by requirements as an alternative.
- Django — rejected without needing to invoke the requirements lock: far too
  heavyweight (ORM, admin, auth scaffolding) for a stateless, no-database,
  no-auth MVP.

**Advantages of FastAPI:**
- Native `async def` route support, which aligns naturally with Playwright's
  async-first Python API — avoids wrapping async browser calls in sync
  adapters that Flask would require (e.g., `asyncio.run()` per request).
- Built-in Pydantic-based request validation for the `/analyze` form fields
  (mode, url, file), giving structured 422 errors for free at the boundary.
- Automatic OpenAPI/Swagger docs (`/docs`, `/openapi.json`) directly satisfy
  the Definition of Done's "API documentation includes endpoint specs,
  request/response examples, error codes" requirement with near-zero extra
  authoring effort.

**Disadvantages/Trade-offs:**
- Slightly newer/less universally known than Flask among some engineers,
  though adoption is now mainstream.
- Returning raw `HTMLResponse` (rather than JSON) is a less common FastAPI
  usage pattern, though fully supported and simple.

**Team Experience:** FastAPI's learning curve is shallow for anyone familiar
with Python type hints; Pydantic models are simple to author for this
project's narrow request surface (a handful of fields).

**Final Decision:** FastAPI, selected within the requirements-approved
FastAPI/Flask choice, primarily for its async-native fit with Playwright and
free OpenAPI documentation.

### Why Uvicorn?

**Alternatives Considered:**
- Hypercorn — comparable ASGI server; rejected only for being less ubiquitous/
  default than Uvicorn in the FastAPI ecosystem, with no feature Locator Lens
  needs that Uvicorn lacks.
- Gunicorn+worker model — unnecessary multi-worker/process complexity given
  the single-threaded, single-analysis-at-a-time constraint.

**Advantages:** Default, well-documented pairing with FastAPI; trivial local
run command (`uvicorn app.main:app`); supports `--reload` for dev iteration.

**Disadvantages/Trade-offs:** Single-process by default (not a concern here —
concurrency beyond one worker is explicitly out of scope).

**Team Experience:** Standard, no learning curve beyond basic CLI flags.

**Final Decision:** Uvicorn, single worker, local host/port only.

### Why Playwright, Chromium-only?

**Alternatives Considered:**
- Selenium WebDriver — rejected: requirements explicitly mandate Playwright.
- Playwright with Firefox/WebKit channels also enabled — rejected: requirements
  explicitly restrict to Chromium engine only, simplifying the render path and
  removing engine-specific `getComputedStyle` discrepancies from scope.
- Headless-only optimization (e.g., minimal Docker Chromium image) — not
  pursued: requirements state headless-mode optimization is not required for
  this dev-only deployment.

**Advantages of Playwright/Chromium:**
- True browser-engine `getComputedStyle` resolution — the most accurate
  possible source for cascade/inheritance-resolved font/color metadata
  (Requirement 5).
- Handles modern SPA frameworks (React/Vue/Angular) out of the box via real
  JS execution and DOM readiness waiting.
- Single dependency covers both "render the page" and "read computed styles
  off live elements," avoiding a second style-resolution engine for the URL
  path.

**Disadvantages/Trade-offs:**
- Adds a heavyweight native browser binary dependency to the dev environment
  (`playwright install chromium`).
- Rendering is inherently slower than static parsing — mitigated by the
  30-second timeout bound already built into the requirements.

**Team Experience:** Playwright's Python API is well-documented; QA
automation engineers (the primary users of this very tool) are typically
already familiar with Playwright from their day-to-day test automation work.

**Final Decision:** Playwright, Chromium channel exclusively, per approved
requirements.

### Why BeautifulSoup4 + lxml?

**Alternatives Considered:**
- Python's built-in `html.parser` — rejected: far less tolerant of malformed
  markup than `lxml`, and requirements explicitly call out BeautifulSoup/lxml.
- `html5lib` parser backend for BeautifulSoup — considered as a more strictly
  spec-compliant tolerant parser; not selected as the primary backend because
  `lxml` is materially faster for the page sizes involved (~5MB ceiling) and
  is explicitly named in the requirements; `html5lib` remains a viable fallback
  if `lxml` ever fails to load a particular malformed document (documented as
  a future consideration, not required for MVP).

**Advantages:**
- Highly tolerant of malformed/incomplete HTML (Requirement 2).
- Fast C-backed parsing suitable for the ~5MB size ceiling.
- Simple, well-known traversal API for locating the 8 target element types.

**Disadvantages/Trade-offs:**
- `lxml` requires a compiled C extension (libxml2/libxslt) — a standard,
  widely available pip-installable wheel on all major platforms, so this is a
  minor setup consideration, not a real blocker.

**Team Experience:** BeautifulSoup is a common, low-learning-curve library
across the Python ecosystem.

**Final Decision:** BeautifulSoup4 with `lxml` backend, per approved
requirements.

### Why Jinja2 for Report Templating?

**Alternatives Considered:**
- Manual Python f-string/string-concatenation HTML building — rejected: no
  templating structure, high risk of missed HTML-escaping leading to broken
  or unsafe report markup; harder to maintain the required table/column
  layout.
- A client-side JS templating/rendering framework (React/Vue) — rejected:
  requirements call for a "lightweight web UI... minimal-JS framework" and
  server-rendered delivery of the report as direct HTML response, not a
  client-side app.

**Advantages:**
- Ships bundled with FastAPI's Starlette dependency chain — zero extra
  install cost.
- Automatic HTML autoescaping by default protects against the analyzed page's
  own content (e.g., element text containing `<script>`) being reflected
  unescaped into the report page (see Security Design).
- Simple, readable template syntax for the metadata header + element table
  layout required by Requirement 6.

**Disadvantages/Trade-offs:** None significant for this scope; Jinja2 is a
mature, stable, minimal-overhead choice.

**Team Experience:** Extremely common in the Python ecosystem; negligible
learning curve.

**Final Decision:** Jinja2 for all report and error-page rendering.

### Why tinycss2 for raw-HTML CSS Cascade Approximation?

**Alternatives Considered:**
- Running Playwright/Chromium against raw HTML too (i.e., always render) —
  rejected: requirements explicitly state raw-HTML mode must analyze "without
  rendering (no JavaScript execution)"; using a real browser to resolve
  styles for this path would violate that requirement.
- `cssutils` — a comparable pure-Python CSS parser; not selected because it
  is less actively maintained than `tinycss2` and has a heavier, older API
  surface for the narrow parsing task needed here (reading `<style>` blocks
  and inline styles).
- Building a hand-rolled minimal CSS tokenizer — rejected: reinventing a
  well-tested wheel for no benefit.

**Advantages:** Lightweight, actively maintained, sufficient for parsing
`<style>` blocks/inline styles to approximate specificity and cascade for the
common cases the raw-HTML path needs to cover.

**Disadvantages/Trade-offs:** Cannot fully replicate a real browser engine's
cascade resolution (e.g., complex selector specificity edge cases, external
stylesheet `@import`, CSS custom properties/variables in unusual contexts).
This is an accepted, documented limitation (see Risks) — the module returns
"Not Available" rather than guessing when resolution is inconclusive, which
is explicitly the behavior Requirement 8 calls for.

**Team Experience:** Small, focused library; minimal learning curve for the
narrow usage required.

**Final Decision:** `tinycss2`, used only for the raw-HTML (non-rendered)
style-resolution path; the URL/rendered path uses the browser's own
`getComputedStyle` and does not depend on this library.

### Why pytest + pytest-playwright + pytest-cov?

**Alternatives Considered:**
- `unittest` (standard library) — rejected: more verbose, weaker fixture
  model, less ecosystem tooling for coverage and async test support compared
  to pytest.
- Live-website integration testing — rejected: requirements explicitly
  mandate "fixture HTML pages or local test server (no live website
  testing)" for integration tests, to keep tests deterministic and fast.

**Advantages:** pytest's fixture system maps cleanly onto reusable HTML
fixtures/mocked Playwright pages; `pytest-cov` directly produces the ≥80%
coverage report required by Definition of Done; `pytest-playwright` provides
first-party support for driving/mocking browser contexts in tests without
hitting real network endpoints.

**Disadvantages/Trade-offs:** None significant; standard, well-supported
choice for this stack.

**Team Experience:** pytest is the de facto standard in the Python testing
ecosystem; broadly familiar.

**Final Decision:** pytest, pytest-asyncio, pytest-playwright, pytest-cov —
all tests use local fixture HTML files or a local test HTTP server, never a
live public website, per approved requirements.

### Why No Containerization for MVP?

**Alternatives Considered:** Docker/Docker Compose packaging — evaluated and
deferred, not rejected outright.

**Advantages of deferring:** Requirements explicitly state "local/dev-only...
no production hardening... no CDN, no load balancing required for MVP" —
adding a container layer now would be effort spent on infrastructure the
requirements do not call for.

**Disadvantages/Trade-offs:** Slightly less "one command" reproducibility for
a brand-new developer machine until Playwright's Chromium binary is installed
locally.

**Team Experience:** N/A — deferred.

**Final Decision:** Plain local Python virtualenv + `uvicorn` process for
MVP; containerization is listed as a Future Consideration, not part of this
architecture.

---

## Data Flow

1. **User submits** a URL or raw HTML/file via the Web UI form (`POST /analyze`).
2. **FastAPI route** validates the request shape (which mode, size limits) and
   acquires the single-analysis lock.
3. **Input Acquisition** resolves the input into a `PageSource`:
   - URL mode: Playwright launches Chromium, navigates (TLS-validated, ≤5
     redirects, ≤30s), captures the live `Page` handle and rendered HTML.
   - Raw HTML mode: input decoded, size-checked, handed directly to the parser
     (no browser launch).
4. **DOM Parsing & Discovery** builds a BeautifulSoup tree (and, if rendered,
   cross-references the live Playwright `Page` for visibility) and yields the
   filtered list of `DiscoveredElement`s.
5. **For each element**, in sequence (single-threaded):
   a. **XPath Generation** computes the locator.
   b. **Style Extraction** resolves font/color/text (only if element has
      visible text).
   Per-element exceptions are caught and recorded as "Failed"/"Skipped" rather
   than aborting the whole analysis.
6. **Report Assembly** combines metadata + all element results into HTML via
   Jinja2.
7. **FastAPI returns** the HTML as the direct response body; the browser
   navigates to and renders it — no client-side fetch/JSON round-trip, no file
   written to disk.
8. **Errors** at any stage are caught by the route handler, mapped to an
   actionable message, and rendered through the same report-shell template as
   an error state (not a raw 500 stack trace).

---

## API Contracts

### `GET /`
Returns the input form page (URL / raw HTML / file upload).

### `POST /analyze`
**Request** (multipart/form-data or x-www-form-urlencoded):
| Field | Type | Required | Notes |
|---|---|---|---|
| `mode` | string enum: `"url"` \| `"raw_html"` | yes | Selects input path |
| `url` | string | required if `mode=url` | Must be http/https |
| `html_text` | string | required if `mode=raw_html` and no file | Pasted markup |
| `html_file` | file upload | required if `mode=raw_html` and no `html_text` | ≤5MB |

**Response — success**: `200 OK`, `Content-Type: text/html`, body = fully
rendered report HTML (per Component 7).

**Response — validation/handled error**: `4xx` (400 for bad input, 408/504-
equivalent handling folded into a 400 with message for timeout, 422 for
malformed request shape), `Content-Type: text/html`, body = rendered error
page using the same report shell, with a human-actionable message
(Requirement 7 examples honored verbatim in message templates).

**Response — unexpected server error**: `500`, generic safe message logged
server-side with full detail; no stack trace leaked to the client (Security
Design).

### `GET /health`
Returns `200 OK` with a minimal JSON `{"status": "ok"}` — operational
liveness check for local dev use; not part of functional requirements but
standard minimal-ops practice with negligible cost.

Full OpenAPI schema is auto-generated by FastAPI at `/docs` and `/openapi.json`
and constitutes the living API documentation artifact.

---

## Security Design

### Authentication
None. Per approved requirements, this is an internal, trusted-network,
local/dev-only tool used by QA/automation engineers; no login or identity
system is implemented. Access control is provided entirely by network
placement (not exposed beyond the developer's/team's local environment).

### Authorization
None. All users of the running instance have full, identical access to both
input modes and the resulting report. There are no roles, permissions, or
per-user data separation, consistent with the "no persistence" design (there
is no "other user's data" to protect against, since nothing is stored).

### Data Protection
- **TLS validation always enforced** for outbound URL fetches — Playwright's
  default certificate validation is never disabled (`ignore_https_errors` is
  never set to `True`); requests to sites with invalid/self-signed certs are
  rejected with a clear error (Requirement 1/7), not silently allowed through.
- **No persistence**: analyzed HTML, discovered elements, and generated
  reports exist only in memory for the duration of a single request/response
  cycle; nothing is written to a database or long-lived file store. This
  eliminates data-at-rest exposure as a concern by design.
- **No secrets**: the application requires no API keys, credentials, or
  tokens (no external services beyond fetching the user-specified target
  URL); nothing to hardcode or leak.
- **Size-bounded processing**: the ~5MB input cap (enforced before parsing,
  for both uploaded/pasted raw HTML and fetched URL responses) bounds memory
  exposure from a maliciously large payload.

### Input Validation (at every entry point)
| Entry point | Validation |
|---|---|
| `url` field | Must parse as a valid URL; scheme restricted to `http`/`https` only (no `file://`, `javascript:`, etc.); malformed input rejected with a specific error before any network call is attempted. |
| Redirect chain | Capped at 5 hops; a 6th redirect aborts the fetch with an actionable error rather than looping indefinitely (SSRF-adjacent hardening: bounds worst-case redirect chains, though full SSRF protection — e.g., blocking internal/RFC1918 target IPs — is out of scope for this internal trusted-network MVP and is called out below as an accepted risk). |
| `html_text` / `html_file` | Size-checked against the ~5MB ceiling before decode/parse; strict UTF-8 decode boundary — non-UTF8/binary content is rejected with a clear `UnparseableContentError`, never silently truncated or guessed at. |
| `mode` field | Restricted via Pydantic `Literal["url", "raw_html"]` — any other value is a 422 at the FastAPI validation layer before pipeline code ever runs. |
| Analyzed page content (element text/attributes) | Treated as untrusted data throughout the pipeline; never `eval`'d, never used to build filesystem paths, never interpolated into shell commands. When rendered into the report, Jinja2's default autoescaping HTML-escapes all text/attribute values pulled from the analyzed page, preventing any `<script>` or event-handler content present in the *analyzed* page from executing in the *report's* rendering context. |

### Threat Analysis

| Threat | Relevance | Mitigation |
|---|---|---|
| Reflected/stored XSS via analyzed page content appearing in the report | Real — the report echoes element text/attributes from arbitrary user-supplied pages | Jinja2 autoescaping on all interpolated values in the report template; never use `\| safe` on analyzed-content fields. |
| SSRF (server fetches attacker-chosen internal URL) | Partially accepted risk — internal trusted-network dev tool, requirements explicitly state "no cross-domain restrictions (no allowlist/blocklist); users can attempt any URL" | Redirect cap (5) and 30s timeout bound the blast radius of any single request; full network-level SSRF protection (blocking RFC1918/loopback targets) is explicitly out of scope for MVP per requirements and is documented here as an accepted risk given the trusted-internal-user threat model, not an oversight. |
| Oversized payload / memory exhaustion (DoS) | Real, low severity given single-user local deployment | ~5MB cap enforced before parsing for both input modes; 30s hard timeout on fetch+render. |
| Malformed/malicious HTML crashing the parser | Real | BeautifulSoup/`lxml` tolerant parsing absorbs malformed markup by design (Requirement 2); truly unparseable (binary/non-UTF8) content is explicitly caught and rejected rather than crashing the process. |
| Path traversal / arbitrary file read via upload handling | Low — file upload is read into memory and never written to or read from a caller-supplied filesystem path | Upload content is streamed directly into the size-check/decode pipeline; no filename from the client is ever used to construct a server-side file path. |
| Information disclosure via stack traces | Real if unhandled | Unexpected exceptions are caught at the FastAPI route boundary, logged in full server-side, and returned to the client as a generic, safe message — never a raw traceback. |
| Credential/secret leakage | Not applicable | No secrets exist in this system (no auth, no external API keys). |
| Man-in-the-middle on outbound fetch | Real if unmitigated | TLS certificate validation is always enforced for URL-mode fetches; never disabled. |

### Compliance
None required. This is an internal exploratory tool processing arbitrary,
user-directed, typically non-sensitive web pages; it does not knowingly
collect, store, or transmit PII, and stores nothing persistently. No
regulatory framework (GDPR, HIPAA, SOC2, etc.) applies given the stated
internal, non-production, non-persistent usage model. Should the tool later
be exposed beyond the internal trusted network or extended to persist data,
this compliance posture must be re-evaluated (see Future Considerations).

---

## Performance & Scalability

- **Performance Targets**: End-to-end analysis (fetch/render + parse + XPath +
  style extraction + report render) within the requirements' ~30s bound for
  the fetch/render portion; parsing/XPath/style/report steps are in-process
  CPU work expected to complete in low single-digit seconds for pages up to
  ~5MB / a few thousand elements.
- **Scalability Approach**: None required by design — single-threaded,
  single-worker Uvicorn process, one analysis at a time enforced by an
  in-process lock. This is a deliberate, requirements-driven choice, not a
  limitation to be engineered around in this phase.
- **Caching Strategy**: None — MVP is stateless; no repeated-analysis caching
  needed given low internal usage volume.
- **Resource Bounds**: Hard ~5MB input/response size cap and 30s timeout are
  enforced at the Input Acquisition boundary to bound memory and wall-clock
  usage per the constraints table.

---

## Reliability & Availability

- **High Availability**: Not applicable — local/dev-only, single instance, no
  redundancy required.
- **Disaster Recovery**: Not applicable — stateless, nothing to back up
  (no database, no persisted analyses).
- **Monitoring**: Basic process-level observation (console output) sufficient
  for dev usage; no APM/metrics stack.
- **Logging**: Python `logging` to console and a local rotating file
  (`logs/locator-lens.log`), capturing request lifecycle, timing, and
  exceptions — satisfies "Basic console/file logging for debugging" constraint.

---

## Deployment Architecture

- **Environment**: Single local/dev environment; no staging/prod tiers
  required for MVP.
- **Deployment Process**: Developer runs `uvicorn app.main:app --reload` (or
  equivalent Make target, see below) after `pip install -r requirements.txt`
  and `playwright install chromium`. No CI/CD pipeline required for MVP beyond
  running lint/tests locally or in a lightweight GitHub Actions check.
- **Version Control**: Standard feature-branch → PR → main workflow, matching
  this repository's existing SDLC orchestrator gates (`documents/` stage
  artifacts, approval gates).

---

## Constraints & Assumptions

**Constraints** (carried forward from approved requirements, not re-litigated):
- Python/FastAPI or Flask backend; Playwright Chromium-only; BeautifulSoup/lxml
  parsing; web-UI report delivery (no downloadable file); hex-color computed
  styles; ID > unique-attribute > relative-XPath priority; ~5MB / ~30s /
  single-threaded performance envelope; local/dev deployment with no auth;
  mocked/fixture-based integration tests only.

**Assumptions**:
- Internal users run modern desktop browsers against a locally-hosted
  instance; no need to support concurrent multi-user load.
- Target pages analyzed are not intentionally adversarial (no hardened
  anti-scraping defenses need to be defeated); this is an internal QA tool.
- "Frontend Technology" auto-detection is best-effort/heuristic and is
  explicitly allowed to report "Not Available" rather than guess.

**Risks**:
1. **Raw-HTML CSS cascade approximation** cannot fully replicate a browser's
   `getComputedStyle` — some style values in raw-HTML mode may be less
   accurate than in rendered mode.
2. **Playwright/Chromium dependency footprint** — first-run download and
   environment setup (browser binaries) adds developer-machine setup steps.
3. **Element-index-based XPath fallback (Priority 3)** may be less stable
   across page revisions than ID-based locators — this is inherent to the
   approved priority strategy, not an implementation defect.
4. **Single in-process lock** means one hung analysis (e.g., unusual page)
   blocks all subsequent requests until it resolves or the 30s timeout fires.

**Mitigation**:
1. Document the raw-HTML limitation explicitly in the report/footer and
   developer guide; keep the cascade resolver simple and honest about
   "Not Available" outcomes rather than producing wrong values.
2. Document setup (`playwright install chromium`) clearly in the deployment
   guide; consider a setup `make` target.
3. Always tag fallback XPaths with the fragility note (already required by
   Requirement 8) so consumers know to double check.
4. Enforce the 30s hard timeout at the Playwright navigation call (and an
   overall pipeline watchdog) so a stuck request cannot exceed the bound;
   release the lock in a `finally` block regardless of outcome.

---

## Future Considerations

- Introduce a background task queue (e.g., Celery/RQ) only if multi-user
  concurrent usage becomes a real requirement — not needed for MVP.
- Add optional report persistence/history if users request re-visiting past
  analyses (would introduce a database layer).
- Add authentication if the tool moves beyond a trusted internal network.
- Containerize (`Dockerfile`) for easier onboarding without changing the
  in-process architecture.
- Consider WebKit/Firefox rendering if cross-browser render-diffing becomes
  a requirement (currently explicitly Chromium-only).

---

**Document Status**: Draft — awaiting design-reviewer approval (Phase 3)
**Author**: solution-architect agent
**Next Step**: Present summary to human reviewer for approval gate decision
