# Implementation Plan: Locator Lens

**Story ID**: EPMCDMETST-62704
**Phase**: 4 — Implementation Planning
**Date**: 2026-08-31
**Status**: Draft — Pending coordinator approval
**Input**: `documents/design-document.md` (Phase 2), `documents/design-review.md`
(Phase 3 — APPROVED WITH CONDITIONS)

---

## 1. Purpose & Scope

This plan decomposes the approved architecture (`documents/design-document.md`)
into an achievable, sequenced set of implementation tasks for the
**implementation-engineer** phase. It also resolves, with a specific named
technical mechanism (not just a risk note), the two "Must Do" conditions
attached to the design-review approval:

1. **Element correlation mechanism** between the BeautifulSoup parse tree and
   Playwright's live DOM (Concern raised against Component 4).
2. **URL-mode ~5MB size-cap enforcement mechanism** during Playwright
   navigation (Concern raised against Component 3).

Both are resolved below in **Section 2 (Resolution of Design-Review Must-Do
Conditions)** and carried into concrete WBS tasks (3.2, 4.2) rather than left
as open risks.

---

## 2. Resolution of Design-Review Must-Do Conditions

### 2.1 Must-Do #1 — Element Correlation Mechanism (BS4 ⇄ Playwright)

**Chosen mechanism: injected marker-attribute scheme (`data-ll-idx`), applied
once, immediately after Playwright navigation/render completes and before any
parsing occurs.**

**How it works:**
1. After `page.goto()` succeeds (rendered/URL mode only — raw-HTML mode never
   has a live Playwright DOM, so no correlation is needed there), execute a
   single `page.evaluate()` script that:
   - Queries the document for every element matching any of the 8 target-type
     CSS selectors (`h1`, `h2,h3,h4,h5,h6`, `a`, `button, input[type=button]`,
     `input`, `select`, `textarea`, `[role=button], [role=menuitem], [role=tab], ...`),
     in DOM (document) order, **excluding** anything inside an `<iframe>`
     content document (the script only walks the top document — iframe
     documents are cross-origin/sandboxed and are already out of scope).
   - Assigns each matched element a sequential integer id via a new attribute
     `data-ll-idx="<N>"` (starting at 0, incrementing per element in DOM
     order). This mutates the *live* DOM only — it does not touch network
     traffic, does not re-fetch the page, and is invisible to the analyzed
     site's own JavaScript (it runs after render, does not conflict with
     framework re-renders since we take the HTML snapshot immediately after).
   - Returns nothing; the mutation is now present in `document`.
2. Immediately call `page.content()` to capture the **post-mutation** HTML
   snapshot — this string now contains the same `data-ll-idx` attributes that
   are also live on the Playwright page. Feed this snapshot (not the
   pre-mutation HTML) into BeautifulSoup/`lxml` for the structural parse.
3. `DiscoveredElement.node_key` = the value of `data-ll-idx` (as a string) for
   every element built from the BS4 tree in rendered mode. This is the "stable
   node handle/index" referenced in the design document, now made concrete.
4. Whenever Component 5 (XPath) or Component 6 (Style) needs the **live**
   Playwright handle for a `DiscoveredElement` (visibility checks, bounding
   box, `getComputedStyle`), it resolves it in O(1) via
   `page.locator(f'[data-ll-idx="{node_key}"]')` — a single attribute-equality
   CSS locator, never a re-derived XPath and never a positional re-scan. This
   guarantees the BS4 node and the Playwright handle refer to the *same*
   physical element for the lifetime of the request.
5. `data-ll-idx` is a synthetic, request-scoped attribute; it is stripped
   from the copy of `attrs` shown in the final report table (never presented
   to the user as if it were a real page attribute) — a one-line filter in
   Component 7 before rendering the "Relevant HTML Attributes" column.
6. Raw-HTML mode: `node_key` is instead the element's stable pre-order index
   in the single BS4 parse tree (no Playwright handle exists to correlate
   with, so a plain positional index is sufficient and cheaper).

**Why this satisfies the condition**: it is a single, request-scoped, O(n)
one-pass injection with O(1) lookup thereafter; it requires no persistent
storage, no XPath round-tripping to re-find elements, and cannot drift because
the BS4 tree is parsed *from* the exact same mutated HTML that the live page
now also carries the markers in.

### 2.2 Must-Do #2 — URL-Mode ~5MB Size-Cap Enforcement Mechanism

**Chosen mechanism: `page.route()` response interception on the main-document
request only, with abort-on-threshold before the body is delivered to the
page.**

**How it works:**
1. Before calling `page.goto(url)`, register
   `page.route(lambda r: r.resource_type == "document", handler)` (scoped to
   `resource_type == "document"` so only the top-level navigation response is
   intercepted — subresources such as images/CSS/JS are not subject to the
   page-size cap, consistent with the requirement's intent of bounding the
   *page* being analyzed).
2. Inside `handler(route)`:
   - Call `response = route.fetch()` to perform the actual network fetch
     under Playwright's control (this still benefits from Playwright's TLS
     validation and redirect following, since `route.fetch()` uses the same
     network stack).
   - Fast path: if `response.headers.get("content-length")` is present and
     exceeds the ~5MB cap, immediately `route.abort()` and raise a typed
     `PageTooLargeError` — no body is ever read into memory.
   - Slow path (no reliable `Content-Length`, e.g., chunked transfer): read
     `body = response.body()` (Playwright buffers the full response to
     provide this API) and check `len(body) > CAP_BYTES` **before** calling
     `route.fulfill()`; if over cap, `route.abort()` and raise
     `PageTooLargeError` instead of fulfilling — the oversized body is
     discarded immediately and never handed to the page/DOM.
   - If within cap: `route.fulfill(response=response)` to let navigation
     proceed normally with the already-fetched body (no double fetch).
3. `PageTooLargeError` is caught by the Input Acquisition module and mapped
   to the same actionable-error contract as other fetch errors (Requirement 7
   / Component 8), e.g., *"Page response exceeded the 5MB analysis limit.
   Try a smaller/simpler page."*
4. This same `page.route()` registration is also the natural place to count
   redirects if the "Should Do #1" verification (Section 6) determines an
   application-level counter is needed in addition to Chromium's own handling
   — the routed handler already sees every navigation-related response.

**Why this satisfies the condition**: it names the exact Playwright API
(`page.route()` + `route.fetch()`/`response.body()` + `route.abort()`/
`route.fulfill()`) rather than the previous outcome-only phrase "streamed
byte counting," and it guarantees an oversized body is never delivered to the
renderer or held longer than necessary to measure it.

---

## 3. Work Breakdown Structure

Effort unit: **person-days (PD)**, 1 PD = ~6 focused hours, single engineer,
sequential single-threaded MVP (no parallel engineering assumed beyond what's
noted). Estimates include implementation + accompanying unit tests for that
task (per Definition of Done, tests are written alongside code, not after).

### Epic 0 — Project Scaffolding & Cross-Cutting Foundations
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 0.1 | Repo/app skeleton | `app/` package layout (`main.py`, `routes/`, `pipeline/`, `templates/`, `static/`), `requirements.txt`, virtualenv setup docs, `Makefile` targets (`setup`, `test`, `lint`, `format`, `run`) | 0.5 PD |
| 0.2 | Exception hierarchy (Component 8) | `InvalidUrlError`, `FetchTimeoutError`, `TlsValidationError`, `UnparseableContentError`, `NoElementsFoundError`, `PageTooLargeError` (new, per §2.2), base `LocatorLensError` | 0.5 PD |
| 0.3 | Logging setup | Console + rotating file handler (`logs/locator-lens.log`), request-lifecycle logging helper | 0.25 PD |
| 0.4 | CI lint/format config | `flake8`/`black`/`isort` config, PEP 8 enforcement, pre-commit-style `make lint`/`make format` | 0.25 PD |

**Epic 0 subtotal: 1.5 PD**

### Epic 1 — Web UI / Entry Form (Component 1)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 1.1 | `GET /` form template | Jinja2 form: URL field, raw-HTML textarea, file upload, mode toggle (vanilla JS only) | 0.5 PD |
| 1.2 | Client-side basic validation | Non-empty check, scheme hint before submit (does not replace server-side validation) | 0.25 PD |
| 1.3 | Base report/error template shell | Shared CSS, print-friendly layout, used by both success report and error pages | 0.5 PD |

**Epic 1 subtotal: 1.25 PD**

### Epic 2 — FastAPI Application Layer (Component 2)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 2.1 | Route definitions | `GET /`, `POST /analyze`, `GET /health` | 0.25 PD |
| 2.2 | Pydantic request models | `mode: Literal["url","raw_html"]`, conditional field requirements, 422 mapping | 0.5 PD |
| 2.3 | Single-analysis lock | In-process `asyncio.Lock` (or `threading.Lock` if sync), acquired at route entry, released in `finally` regardless of outcome | 0.5 PD |
| 2.4 | Exception → HTTP/response mapping | Maps each typed exception (incl. `PageTooLargeError`) to actionable message + status code, rendered via shared error-shell template | 0.5 PD |
| 2.5 | Request-lifecycle logging integration | Wire Epic 0.3 logger into route entry/exit, timing, exception logging | 0.25 PD |

**Epic 2 subtotal: 2.0 PD**

### Epic 3 — Input Acquisition Module (Component 3)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 3.1 | URL validation | Scheme allowlist (http/https only), format validation via `urllib.parse`, reject `file://`/`javascript:`/etc. before any network call | 0.5 PD |
| **3.2** | **URL-mode size-cap enforcement (Must-Do #2)** | Implement `page.route()` interception scoped to `resource_type == "document"`; fast-path `Content-Length` check; slow-path `response.body()` length check; `route.abort()` + `PageTooLargeError` on breach; `route.fulfill()` on pass. Unit tests using a local test server serving controlled-size/chunked responses (per requirements' "no live website testing" rule). | 1.5 PD |
| 3.3 | Playwright navigation orchestration | `page.goto(url, wait_until="networkidle")`, 30s combined fetch+render timeout (Playwright's own `timeout=` param + wrapping watchdog), TLS validation left at Playwright default (never set `ignore_https_errors=True`) | 1.0 PD |
| 3.4 | Redirect handling + verification spike | Verify Chromium/Playwright's actual redirect-count exposure (Should-Do #1 from design review); if not natively cappable, add an application-level counter inside the same `page.route()` handler from 3.2 | 1.0 PD |
| 3.5 | Render-failure fallback | On Playwright render/timeout failure, fetch raw response body (reusing the size-capped fetch path) and parse as static HTML; set `degraded=True` on `PageSource` | 0.75 PD |
| 3.6 | Raw-HTML/upload path | Decode as UTF-8 with strict error handling → `UnparseableContentError` on failure/binary; pre-decode ~5MB size check (streamed read, abort early) | 0.75 PD |
| 3.7 | `PageSource` value object + unit tests | `{html, mode, source_label, rendered, degraded}`; full unit-test suite for 3.1–3.6 | 0.5 PD |

**Epic 3 subtotal: 6.0 PD**

### Epic 4 — DOM Parsing & Element Discovery Module (Component 4)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| **4.1** | **Marker-injection script (Must-Do #1, rendered path)** | `page.evaluate()` script assigning sequential `data-ll-idx` to all 8-type matches in DOM order, excluding iframe-nested content; capture `page.content()` snapshot immediately after | 1.0 PD |
| **4.2** | **Correlation utility (Must-Do #1, shared)** | `resolve_live_handle(node_key) -> Locator` helper (`page.locator(f'[data-ll-idx="{node_key}"]')`); raw-HTML positional-index `node_key` assignment; `DiscoveredElement.node_key` field on both paths | 0.5 PD |
| 4.3 | BS4/lxml tree construction | Parse the (possibly marker-mutated) HTML with `BeautifulSoup(html, "lxml")`; tolerant-parse error handling → `UnparseableContentError` only for true binary/non-UTF8 | 0.5 PD |
| 4.4 | 8-element-type matcher | Selectors/traversal for headings, subheadings, links, buttons, inputs, selects, textareas, clickable roles | 1.0 PD |
| 4.5 | Exclusion rules | display:none / visibility:hidden / aria-hidden (computed via live handle when rendered, inline/style heuristic when static); iframe descent prevention (never traverse into `<iframe>` subtree, same- or cross-domain); viewport-intersection check via `is_visible()` (rendered only) | 1.25 PD |
| 4.6 | `DiscoveredElement` model + unit tests | Tag, attrs, text, `node_key`, type classification; unit tests against fixture HTML pages covering all 8 types + exclusions | 1.0 PD |

**Epic 4 subtotal: 5.25 PD**

### Epic 5 — XPath Generation Module (Component 5)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 5.1 | Priority 1 — ID-based | Uniqueness check across document; `//*[@id='...']` | 0.25 PD |
| 5.2 | Priority 2 — unique attribute-based | `name`, `data-testid`, `aria-label` uniqueness check; `//tag[@attr='value']` | 0.5 PD |
| 5.3 | Priority 3 — shortest robust relative XPath | Tag + normalized text and/or position-index fallback; readability preference over absolute paths | 1.0 PD |
| 5.4 | Fragility tagging | `fragile=True` + "** Fragile **" note when no robust identifier found | 0.25 PD |
| 5.5 | Syntax validation | Round-trip every generated XPath through `lxml.etree.XPath()` before returning; unit tests | 0.5 PD |

**Epic 5 subtotal: 2.5 PD**

### Epic 6 — Style Metadata Extraction Module (Component 6)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 6.1 | Rendered-mode extraction | Batch `page.evaluate("el => getComputedStyle(el)")` per element via `resolve_live_handle` (Epic 4.2); font family/size/color/text extraction | 1.0 PD |
| 6.2 | Raw-HTML-mode cascade approximation | `tinycss2`-based `<style>`/inline-style parsing, basic specificity resolution; "Not Available" on inconclusive resolution (never guess) | 1.5 PD |
| 6.3 | Color normalization utility | `rgb()`/named-color → `#RRGGBB` hex, shared by both paths | 0.5 PD |
| 6.4 | `StyleResult` model + unit tests | Includes edge cases: pseudo-elements, CSS variables, fallback fonts | 1.0 PD |

**Epic 6 subtotal: 4.0 PD**

### Epic 7 — Report Assembly & Rendering Module (Component 7)
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 7.1 | Metadata auto-detection | App name (`<title>` → URL host → "Not Available"); frontend tech (meta tags, `__NEXT_DATA__`, `ng-version`, `data-reactroot`, Vue signatures → "Not Available") | 1.0 PD |
| 7.2 | Element Analysis Table rendering | 8 required columns incl. attribute filtering to strip synthetic `data-ll-idx` (per §2.1 step 5); "Failed"/"Skipped" row flagging with reason | 1.0 PD |
| 7.3 | Report header/metadata block | Timestamp, page source label, element counts by type, degradation notice | 0.5 PD |
| 7.4 | Consistent "Not Available" styling | Shared CSS class/visual treatment across all missing-data cases (AC8) | 0.25 PD |
| 7.5 | `render_report()` integration + unit tests | Full pipeline glue test with fixture data | 0.75 PD |

**Epic 7 subtotal: 3.5 PD**

### Epic 8 — Testing, Documentation & Release Readiness
| # | Task | Subtasks | Effort |
|---|---|---|---|
| 8.1 | Integration test suite | Fixture HTML pages + local test HTTP server (no live-site testing); end-to-end URL-mode and raw-HTML-mode flows | 1.5 PD |
| 8.2 | Coverage verification | `pytest-cov` run, close gaps to reach ≥80% overall / prioritize critical paths (validation, parsing, discovery, XPath, style) | 0.75 PD |
| 8.3 | Lint/format pass | `flake8`/`black`/`isort` clean run across codebase | 0.25 PD |
| 8.4 | Developer guide | Architecture overview, key patterns (marker-injection correlation, size-cap interception), extension guide | 0.75 PD |
| 8.5 | Deployment guide | Setup steps (`pip install`, `playwright install chromium`), env config, local run instructions | 0.5 PD |
| 8.6 | API documentation | Verify FastAPI auto-generated OpenAPI covers all fields/errors; supplement with example request/response snippets | 0.25 PD |
| 8.7 | README update | Feature overview, usage instructions | 0.25 PD |

**Epic 8 subtotal: 4.25 PD**

### Grand Total
| Epic | Effort (PD) |
|---|---|
| 0 — Scaffolding & Cross-Cutting | 1.5 |
| 1 — Web UI | 1.25 |
| 2 — FastAPI App Layer | 2.0 |
| 3 — Input Acquisition | 6.0 |
| 4 — DOM Parsing & Discovery | 5.25 |
| 5 — XPath Generation | 2.5 |
| 6 — Style Extraction | 4.0 |
| 7 — Report Assembly | 3.5 |
| 8 — Testing/Docs/Release | 4.25 |
| **Total** | **30.25 PD** |

At 1 engineer, 5 PD/week nominal velocity (accounting for review cycles,
context switching): **≈ 6.5 working weeks**, rounded to **7 weeks** with
buffer (see Timeline).

---

## 4. Task Dependencies

```
Epic 0 (Scaffolding) ──────────────────────────────────────────────────┐
   │                                                                    │
   ▼                                                                    │
Epic 2 (FastAPI App Layer) ◀── depends on Epic 0.2 (exceptions),       │
   │                            Epic 0.3 (logging)                     │
   │                                                                    │
   ├──▶ Epic 1 (Web UI) ── can proceed in parallel with Epic 3 once     │
   │                        Epic 2.1 routes exist (independent track)  │
   │                                                                    │
   ▼                                                                    │
Epic 3 (Input Acquisition) ◀── depends on Epic 0.2 (PageTooLargeError) │
   │      3.2 (size-cap) and 3.3 (navigation) are prerequisite          │
   │      to 3.4 (redirect spike) and 3.5 (fallback)                   │
   ▼                                                                    │
Epic 4 (DOM Parsing & Discovery) ◀── depends on Epic 3 (PageSource)    │
   │      4.1 (marker injection) MUST land before 4.3 (BS4 parse of    │
   │      the mutated snapshot) and before 4.2 (correlation utility    │
   │      needs 4.1's attribute scheme to exist)                       │
   │      4.5 (exclusions) depends on 4.2 (live-handle resolution      │
   │      for visibility checks)                                       │
   ▼                                                                    │
   ├──▶ Epic 5 (XPath Generation) ◀── depends on Epic 4 (DiscoveredElement)
   │                                                                    │
   └──▶ Epic 6 (Style Extraction) ◀── depends on Epic 4.2 (correlation │
                                        utility, for rendered-mode      │
                                        getComputedStyle calls)         │
                                                                         │
Epic 5 + Epic 6 outputs ──▶ Epic 7 (Report Assembly) ──▶ Epic 8 (Tests/Docs)
                                                                         │
Epic 0 also feeds Epic 8.4/8.5 (docs reference scaffolding/Makefile) ◀──┘
```

**Key dependency notes:**
- Task **3.2** (size-cap mechanism) is a hard prerequisite for **3.3**
  (navigation), since the `page.route()` handler must be registered *before*
  `page.goto()` is called.
- Task **4.1** (marker injection) is a hard prerequisite for **4.2**
  (correlation utility) and **4.3** (BS4 parse must consume the
  *post-injection* snapshot, not the pre-injection HTML) — sequencing within
  Epic 4 is not reorderable.
- Epic 5 and Epic 6 are mutually independent once Epic 4 is complete and may
  be developed in either order (or in parallel if a second engineer is
  available); both are prerequisites for Epic 7.
- Epic 1 (Web UI) has no dependency on Epics 3–7 internals — only on Epic 2's
  route existing — so it can be built early/in parallel to keep the critical
  path clear.

---

## 5. Critical Path & Timeline

**Critical path** (longest dependency chain, drives minimum completion time):

```
Epic 0 (1.5 PD)
  → Epic 2 (2.0 PD)
    → Epic 3 [3.1 → 3.2 → 3.3 → 3.4 → 3.5 → 3.6 → 3.7] (6.0 PD)
      → Epic 4 [4.1 → 4.2 → 4.3 → 4.4 → 4.5 → 4.6] (5.25 PD)
        → Epic 6 (4.0 PD)  [longer of Epic 5 (2.5) / Epic 6 (4.0)]
          → Epic 7 (3.5 PD)
            → Epic 8 (4.25 PD)
```

**Critical path length**: 1.5 + 2.0 + 6.0 + 5.25 + 4.0 + 3.5 + 4.25 =
**26.5 PD**. This figure treats Epic 1 (1.25 PD) and Epic 5 (2.5 PD) as
off-critical-path slack — which is only true if a **second engineer** picks
up Epic 1 and/or Epic 5 while the first engineer continues along the
Epic 0→2→3→4→6→7→8 chain.

**Single-engineer caveat**: this plan assumes **one engineer** working
sequentially (per Section 4's note that Epic 5 and Epic 6 "may be developed
in either order, or in parallel if a second engineer is available"). A single
engineer cannot run Epic 5 and Epic 6 concurrently, so the 26.5 PD
critical-path figure above is **not** the realistic duration for this plan.
The realistic single-engineer duration is the **full sum of all epic
effort, 30.25 PD**, executed in one continuous sequence (Epic 0 → 2 → 1 → 3 →
4 → 5 → 6 → 7 → 8). At 5 PD/week this is **6.05 weeks of pure task effort**,
to which schedule buffer (review cycles, the redirect-verification spike in
3.4, and general slip risk on Epic 4 per R6 in Section 6) is added to reach
the **≈7-week** estimate used for milestones below. The 26.5 PD critical path
only becomes an achievable duration if a second engineer is added to take
Epic 1 and/or Epic 5 off the primary engineer's plate.

### Milestones (single engineer, sequential order Epic 0 → 2 → 1 → 3 → 4 →
5 → 6 → 7 → 8, 5 PD/week, start Monday 2026-09-07 pending this plan's
approval)

Target dates below are derived directly from cumulative person-days elapsed
since 2026-09-07, at 5 PD (working days) per week, so they are internally
consistent with the WBS effort totals in Section 3:

| Milestone | Cumulative PD | Target Completion | Epics Covered |
|---|---|---|---|
| M1: Scaffolding + App Layer ready | 4.75 PD | End of Week 1 (Fri 2026-09-11) | Epic 0, Epic 2, Epic 1 |
| M2: Input Acquisition complete (incl. size-cap mechanism, Must-Do #2) | 10.75 PD | Start of Week 3 (Mon 2026-09-21) | Epic 3 |
| M3: DOM Discovery complete (incl. correlation mechanism, Must-Do #1) | 16.0 PD | Start of Week 4 (Mon 2026-09-28) | Epic 4 |
| M4: XPath + Style extraction complete | 22.5 PD | Mid Week 5 (Wed 2026-10-07) | Epic 5, Epic 6 (sequential — Epic 5 then Epic 6) |
| M5: Report Assembly complete | 26.0 PD | Start of Week 6 (Mon 2026-10-12) | Epic 7 |
| M6: Testing, docs, coverage ≥80%, release-ready | 30.25 PD | Start of Week 7 (Mon 2026-10-19); pure task effort | Epic 8 |

**Total timeline: ≈7 calendar weeks.** Pure sequential task effort
(30.25 PD ÷ 5 PD/week = 6.05 weeks) reaches M6 by Monday 2026-10-19; adding
the schedule buffer noted above (review cycles, verification spikes, Epic 4
slip risk) extends the realistic target completion to the **end of Week 7
(Fri 2026-10-23)**. The previously-cited 26.5 PD critical path is achievable
only with a second engineer absorbing Epic 1 and/or Epic 5 in parallel; for
the single-engineer staffing this plan assumes, 30.25 PD (plus buffer) is the
governing figure.

---

## 6. Risk Assessment & Mitigation

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Redirect-count verification (Should-Do #1)** — Playwright/Chromium may not expose a directly cappable redirect counter, requiring an app-level counter layered into the Epic 3.2 `page.route()` handler | Medium | Low-Medium | Scheduled explicitly as Task 3.4 early in Epic 3, before dependent Epic 4 work begins; time-boxed spike (0.5 PD of the 1.0 PD task); fallback design (app-level counter in the same route handler) already identified in §2.2 step 4 |
| R2 | **Marker-injection interferes with framework re-render** — if a SPA re-renders after the `page.evaluate()` injection but before `page.content()` is captured, `data-ll-idx` attributes could be stripped/reordered | Low | Medium | Capture `page.content()` immediately (synchronously) after injection in the same `page.evaluate()` round-trip context; add a unit/integration test using a React fixture that re-renders on an interval to confirm marker survival within the capture window |
| R3 | **Raw-HTML CSS cascade approximation inaccuracy** (carried forward from design review, accepted risk) | Medium | Low | `tinycss2` resolver returns "Not Available" rather than guessing (Epic 6.2); documented explicitly in developer guide (Epic 8.4) and report degradation notice |
| R4 | **Single in-process lock causes request queuing/perceived hang** on a slow/stuck analysis | Low | Medium | 30s hard timeout wraps the Playwright navigation call (Epic 3.3); lock release guaranteed via `finally` (Epic 2.3) |
| R5 | **`page.route()` interception (Epic 3.2) double-buffers large responses in memory** before the abort decision on the slow path (no `Content-Length`) | Medium | Medium | Fast path (`Content-Length` header check) avoids buffering whenever the header is present/trustworthy; document as an accepted bounded-worst-case behavior (worst case is bounded by the ~5MB cap itself, since `response.body()` is only read once per navigation, not per chunk-without-limit) |
| R6 | **Effort underestimation on Epic 4 (marker injection + correlation)** given it is new, review-driven design work with no prior implementation to reference | Medium | Medium | 1.5 PD buffer already included in Epic 4 estimate versus a "naive" 3.75 PD sum of subtasks; flagged as the epic most likely to slip — monitor at M3 checkpoint |
| R7 | **Playwright/Chromium first-run setup friction** on a new developer machine | Low | Low | `playwright install chromium` documented as an explicit Makefile target and first line of deployment guide (Epic 8.5) |
| R8 | **Coverage gap at ≥80% threshold** if edge-case branches (fragile-XPath, degraded-mode, malformed-HTML paths) are under-tested during initial implementation | Medium | Medium | Dedicated Epic 8.2 task with buffer to close gaps after initial suite is written, rather than assuming first-pass tests hit 80% |

No risk identified above is rated **High likelihood + High impact**; none
requires escalation back to the design-reviewer or solution-architect phases
per the design review's own instruction that these conditions be resolved at
the implementation-planning level.

---

## 7. Approval Gate

Per `CLAUDE.md` and `.claude/rules/approval-gate-rules.md`, this
implementation plan requires **human approval** before the
**implementation-engineer** phase begins.

**Approval criteria** (from `.claude/agents/implementation-planner.md`):
- ✓ Work breakdown is complete and achievable — 8 epics, 45 tasks, WBS above.
- ✓ Dependencies properly sequenced — Section 4.
- ✓ Effort estimates are realistic — 30.25 PD, with explicit buffer called out
  on the highest-uncertainty epic (Epic 4).
- ✓ Timeline is acceptable — 7-week estimate, low priority/exploratory
  project per requirements.
- ✓ Both design-review Must-Do conditions are resolved with a named,
  concrete technical mechanism and represented as explicit WBS tasks (3.2,
  4.1, 4.2), not merely restated as risks.

**Gate status**: Pending coordinator review and decision. Upon approval,
`documents/.approval-gates/04-implementation-plan-approved.txt` will be
created and Phase 5 (**implementation-engineer**) begins. If rejected,
specific feedback will be incorporated and this document resubmitted.

---

**Document Status**: Complete — awaiting coordinator approval
**Author**: implementation-planner agent
**Next Step (pending approval)**: Create approval-gate checkpoint;
implementation-engineer begins Phase 5.
