# Locator Lens — Project Intelligence

<!-- BEGIN AUTO-GENERATED PROJECT INTELLIGENCE -->
Last Sync: 2026-09-08 21:03:03

## Application Overview

Locator Lens is a local/dev-only FastAPI service that analyzes a webpage (URL or raw HTML), discovers UI elements, generates prioritized XPath and CSS locators, extracts static style metadata, and renders an HTML report in the browser. It parses server-delivered HTML only — JavaScript is not executed.

## Business Purpose

Helps QA engineers and test automation developers inspect a page's static structure and identify stable, deterministic locators for headings, links, buttons, inputs, dropdowns, textareas, and role-based clickable elements. Value: fast local analysis, deterministic locator output, and traceable MVP validation.

## Architecture Summary

Single-process, stateless FastAPI service. Users submit exactly one input: an HTTP/HTTPS URL or raw HTML. URL inputs are fetched with bounded redirects and explicit timeouts. HTML is parsed via BeautifulSoup/lxml; independent read-only pipeline stages extract elements, resolve static styles, detect technology, generate locators, and render a Jinja2 report. No database, authentication, queue, background worker, or persisted state.

## Technology Stack

- Python / FastAPI (uvicorn)
- BeautifulSoup4 + lxml — HTML parsing
- requests — URL fetching
- Playwright — browser-rendered analysis
- Jinja2 — report templating
- pytest — test suite
- GitHub Actions — CI/CD, CodeQL security scanning
- Claude Code agents, skills, MCP integrations — SDLC governance

## Feature Catalog

- Accepts exactly one input: URL or raw HTML
- Validates URL syntax (HTTP/HTTPS only)
- Follows redirects up to configured limit; reports final resolved URL
- Explicit request timeouts (connect + read)
- Parses malformed HTML tolerantly
- Extracts: headings (visible + ARIA), links, buttons, inputs, selects, textareas, ARIA-role elements, tabindex >= 0 elements
- Deduplicates elements matched by multiple rules
- Normalizes visible text (trims, collapses whitespace)
- Excludes statically hidden elements (hidden attr, aria-hidden="true", display:none, visibility:hidden)
- Resolves font family, font size, text color from inline styles + embedded/linked CSS
- Detects React, Vue, Angular, Bootstrap, WordPress, and generator metadata
- Generates one preferred locator per element (priority: id → name → data-testid → XPath → CSS)
- Marks non-unique locators
- Renders safe HTML reports via Jinja2 autoescaping with clear empty/error/missing-data states

## Source Code Map

<!-- BEGIN:source-code-map -->
src/app/__init__.py
src/app/color_utils.py
src/app/exceptions.py
src/app/logging_config.py
src/app/main.py
src/app/models.py
src/app/pipeline/__init__.py
src/app/pipeline/discovery.py
src/app/pipeline/input_acquisition.py
src/app/pipeline/pipeline.py
src/app/pipeline/report.py
src/app/pipeline/style_extract.py
src/app/pipeline/tech_detect.py
src/app/pipeline/xpath_gen.py
src/app/routes.py
src/app/templates/base.html
src/app/templates/error.html
src/app/templates/form.html
src/app/templates/report.html
<!-- END:source-code-map -->

| File | Responsibility |
|---|---|
| `src/app/main.py` | FastAPI entry point and app setup |
| `src/app/models.py` | Immutable result contracts used by the pipeline |
| `src/app/routes.py` | HTTP route handlers |
| `src/app/exceptions.py` | Custom exception types |
| `src/app/color_utils.py` | Color parsing utilities |
| `src/app/logging_config.py` | Structured logging setup |
| `src/app/pipeline/pipeline.py` | Analysis pipeline orchestration |
| `src/app/pipeline/input_acquisition.py` | URL fetch, HTML input handling, redirect/timeout controls |
| `src/app/pipeline/discovery.py` | Element extraction, categorization, deduplication |
| `src/app/pipeline/style_extract.py` | Static CSS style resolution |
| `src/app/pipeline/tech_detect.py` | Technology signature detection |
| `src/app/pipeline/xpath_gen.py` | Locator candidate generation, scoring, tie-breaking |
| `src/app/pipeline/report.py` | HTML report rendering |
| `src/app/templates/` | Jinja2 input form, report, error, and base templates |

## Design Decisions

- Stateless and synchronous MVP — no unnecessary infrastructure
- Static HTML analysis only — deterministic, lightweight, no browser dependency for core flow
- Explicit redirect and timeout controls — no indefinite network waits
- One deterministic locator per element over large alternative lists
- Relative XPath before CSS fallback; stable attributes and normalized text preferred
- Jinja2 autoescaping — analyzed page data never rendered as trusted HTML
- Full traceability via SDLC artifacts in `documents/` and approval gates in `documents/.approval-gates/`

## Known Limitations

- JavaScript not executed; dynamically injected content excluded
- Browser-computed styles and layout-dependent visibility not inferred
- Static CSS support bounded; uncertain values return "Not available"
- Technology detection is signature-based; may return "Not detected"
- SSRF protection, private-network blocking, rate limiting, authentication, and production hardening deferred
- Large DOM performance not explicitly resource-bounded beyond MVP assumptions
- Redirect-chain reporting out of scope; only final resolved URL reported

## Future Enhancements

- SSRF protections and private-network address blocking before hosted deployment
- Response-size, DOM-size, CSS-size, and processing-time limits
- Structured logging and production observability
- Optional Playwright-rendered analysis for JavaScript-heavy pages
- Expanded CSS cascade/computed-style support
- Unicode locator tests and large-DOM performance benchmarks

## SDLC Sync Notes

<!-- BEGIN:sdlc-sync -->
- documents/requirements.md - exists (updated 2026-09-08 20:55)
- documents/design-document.md - exists (updated 2026-09-08 20:55)
- documents/design-review.md - exists (updated 2026-09-08 20:55)
- documents/implementation-plan.md - not yet generated
- documents/implementation-summary.md - exists (updated 2026-09-08 20:55)
- documents/code-review.md - exists (updated 2026-09-08 20:55)
- documents/qa-report.md - exists (updated 2026-09-08 20:55)
- documents/pull-request.md - exists (updated 2026-09-08 20:55)
<!-- END:sdlc-sync -->

Hook: `.claude/hooks/update-rag.ps1` (PostToolUse — triggers on `Write`/`Edit` to `documents/`, `src/`, or `README.md`)

<!-- END AUTO-GENERATED PROJECT INTELLIGENCE -->

## Human-Maintained Notes

Add project-specific retrieval notes here. This section is preserved by the synchronization hook.
