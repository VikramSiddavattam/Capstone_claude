# Design Review: Locator Lens

## Review Date: 2026-08-31
## Reviewed By: design-reviewer agent (automated architecture review, Phase 3)
## Input Reviewed: `documents/design-document.md` (Phase 2, solution-architect)
## Reference: `documents/requirements.md` (Phase 1, approved 2026-08-31)

---

## Executive Summary

The proposed architecture is a single-process, stateless FastAPI application with
eight cohesive Python modules (Web UI, API/Orchestration, Input Acquisition, DOM
Parsing & Discovery, XPath Generation, Style Extraction, Report Assembly, and
cross-cutting Error Handling/Logging). It maps cleanly to all 9 functional
requirements and all 9 acceptance criteria, uses only the technology choices
already locked by the approved requirements (Python/FastAPI, Playwright/Chromium,
BeautifulSoup4/lxml, web-UI HTML delivery), and correctly declines to introduce
complexity (auth, database, queuing, multi-worker scaling) that the requirements
explicitly rule out.

The design is thorough, self-aware of its own limitations (raw-HTML CSS
approximation, SSRF accepted risk, single-lock contention), and each such
limitation is already paired with a documented mitigation or explicit
risk-acceptance rationale tied back to requirement text. No critical security,
scalability, or feasibility blockers were found. Two implementation-level gaps
were identified that must be resolved with a concrete technical approach during
Phase 4 (implementation-planner) / Phase 5 (implementation-engineer), but neither
invalidates the architecture itself.

**Recommendation: APPROVE WITH CONDITIONS** (see Recommendations → Must Do).

---

## Feasibility Assessment

### Strengths
- Component boundaries map 1:1 to distinct requirements (Input Acquisition ↔
  Req 1/2, Discovery ↔ Req 3, XPath ↔ Req 4, Style ↔ Req 5, Report Assembly ↔
  Req 6, Error Handling ↔ Req 7/8, single-lock ↔ Req 9), which makes the design
  easy to implement, test, and review incrementally.
- All technology choices were either directly mandated by the approved
  requirements or justified with alternatives-considered analysis (FastAPI vs.
  Flask, Uvicorn vs. Hypercorn, tinycss2 vs. cssutils, etc.) — nothing
  speculative or unjustified.
- The design explicitly refuses unnecessary complexity (no containerization, no
  task queue, no multi-worker) consistent with the MVP/local-dev-only scope —
  this is the correct feasibility posture for a low-priority exploratory tool.
- The team's stated user base (QA/automation engineers) is already familiar with
  Playwright and Python, reducing implementation risk.
- Per-element exception handling (catch-and-mark-"Failed", not pipeline-fatal)
  is a sound, testable approach to the partial-failure requirement (Req 6/AC6).

### Concerns
- **Dual-DOM-representation node correlation** (Component 4): the design
  proposes building a BeautifulSoup tree for structure/attributes while also
  querying "live Playwright DOM handles" for visibility on rendered pages, and
  says discovered elements carry "a stable node handle/index for downstream
  XPath and style extraction." BeautifulSoup's parse tree and Playwright's live
  page are two independent representations of the DOM; the document does not
  specify the concrete mechanism that keeps a given `DiscoveredElement`'s BS4
  node and its corresponding Playwright `ElementHandle`/`Locator` referring to
  the *same* element (e.g., an injected `data-locator-lens-id` attribute, or
  positional/XPath-based lookup performed once and reused). Without this
  concrete correlation strategy, Components 4, 5, and 6 cannot be implemented
  consistently. **This must be resolved with a specific approach before/at the
  start of implementation** (see Recommendations → Must Do #1).
- **5MB size cap enforcement during Playwright navigation** (Component 3): for
  raw-HTML/upload input, streaming size-checking before decode is straightforward.
  For URL mode, the document states the cap is enforced "via `Response`
  content-length and streamed byte counting," but Playwright's `page.goto()`
  does not natively expose a byte-streaming hook — achieving this requires
  explicit use of Playwright's request/response interception (`page.route()` /
  `response.body()` size-checking) or an abort-on-threshold handler, which is a
  non-trivial but well-known pattern. The document should have named this
  mechanism explicitly rather than describing the *outcome* ("streamed byte
  counting") without the *mechanism*. **Not a design flaw, but an
  under-specified implementation detail that must be spelled out in the
  implementation plan** (see Recommendations → Must Do #2).

### Critical Issues
None. Both concerns above are resolvable implementation-detail gaps, not
architectural defects — they do not require the solution-architect to revise
the design's component boundaries, technology choices, or data flow.

---

## Security Assessment

### Secure Aspects
- Authentication/authorization correctly and explicitly omitted with clear
  rationale (trusted internal network, no persisted data to protect),
  consistent with requirements' explicit "None required" constraints.
- TLS certificate validation is explicitly always-on (`ignore_https_errors`
  never set `True`) — correctly enforces Requirement 1's TLS mandate.
- XSS mitigation is concrete and correct: Jinja2 default autoescaping applied
  to all analyzed-page-derived content (element text/attributes) reflected into
  the report, with an explicit rule to never use the `| safe` filter on
  untrusted fields. This is the right control for a tool whose entire purpose
  is to echo arbitrary third-party page content back into an HTML report.
- No secrets/credentials exist anywhere in the system — correctly identified as
  not applicable.
- Size-bounded processing (~5MB) and 30s timeout bound both memory and
  wall-clock exposure to hostile or oversized input.
- Upload handling reads content into memory only; no client-supplied filename
  is ever used to construct a server-side path — path traversal is correctly
  ruled out by design, not by a filter.
- Unexpected exceptions are mapped to a generic client-safe message at the
  route boundary, with full detail logged server-side only — correct
  information-disclosure control.

### Questions
- The redirect-cap mitigation (5 hops) and SSRF risk-acceptance are reasonable,
  but the document should confirm in the implementation plan whether Playwright
  navigation actually surfaces/enforces a redirect count that can be checked
  against 5 (Chromium's own default max-redirects behavior differs from an
  explicit application-level counter) — flagged as a verification item, not a
  security gap, since the risk is already explicitly accepted per the
  no-allowlist/no-blocklist requirement.

### Critical Security Issues
None. SSRF is a deliberate, requirements-driven, explicitly-documented accepted
risk (internal trusted-network tool, requirements forbid domain
allow/blocklisting) rather than an oversight — this is the correct way to
handle a risk the business has already decided not to mitigate.

---

## Performance & Scalability

### Good
- Performance targets are grounded in the requirements' own 30s/~5MB envelope,
  not invented independently.
- Correctly identifies that the bottleneck is network fetch/render time, not
  Python CPU time, and does not over-engineer around a bottleneck that doesn't
  exist for this scope.
- Single-analysis-lock design directly satisfies Requirement 9's
  single-threaded MVP mandate, with an explicit note that the lock is released
  in a `finally` block regardless of outcome — good defensive detail against
  a stuck/deadlocked service.
- No caching, no scaling, no HA — all correctly justified as unnecessary for a
  local/dev-only, single-user-at-a-time internal tool. Avoiding speculative
  scalability work here is the right call, not a gap.

### Questions
- None outstanding beyond the redirect-verification item already noted above.

### Concerns
- The single in-process lock is correctly identified by the architect as a
  risk (one hung analysis blocks all others until the 30s timeout fires) with
  an already-documented mitigation (hard timeout at the Playwright navigation
  call plus a `finally`-block lock release). This is adequate for MVP scope and
  requires no further design change.

---

## Standards Compliance

- **Modularity/SOLID**: Each of the 8 components has a single, clearly bounded
  responsibility (Input Acquisition does not parse; DOM Parsing does not
  generate XPaths; XPath Generation does not touch styles), consistent with
  CLAUDE.md's Single Responsibility guidance.
- **Testability**: Every module is specified with a pure-function-style
  interface (`generate_xpath(...)`, `extract_style(...)`, `render_report(...)`)
  suitable for unit testing in isolation, and the test strategy (pytest,
  pytest-cov, fixture-based/local-server integration tests, no live-site
  testing) directly satisfies the Definition of Done's ≥80% coverage and
  "fixture HTML pages or local test server (no live website testing)"
  constraints.
- **Documentation**: FastAPI's auto-generated OpenAPI/Swagger docs satisfy the
  API documentation requirement with near-zero extra authoring burden;
  deployment guide and developer guide are explicitly planned deliverables in
  the Deployment Architecture section.
- **Error handling at boundaries**: A typed exception hierarchy
  (`InvalidUrlError`, `FetchTimeoutError`, `TlsValidationError`,
  `UnparseableContentError`, `NoElementsFoundError`) mapped to actionable
  messages at the FastAPI route boundary matches CLAUDE.md's "explicit error
  handling at system boundaries; fail fast on invalid input" principle.
- **Maintainability**: Technology choices favor mainstream, well-documented,
  low-learning-curve libraries (Jinja2, pytest, BeautifulSoup) over novel or
  exotic tooling, in line with "Clarity Over Cleverness."

No deviations from organizational standards were identified.

---

## Risk Analysis

### High Risk
- **Dual-DOM node correlation approach undefined** (see Feasibility →
  Concerns). Mitigation: require the implementation plan to name the specific
  correlation mechanism (e.g., injected marker attribute or single
  XPath-derived lookup key shared by both representations) before coding
  Components 4–6.

### Medium Risk
- **URL-mode size-cap enforcement mechanism under-specified**. Mitigation:
  implementation plan must name the specific Playwright interception pattern
  (e.g., `page.route()` + response size check, or `Content-Length` header
  pre-check with abort) used to bound memory before/while a JS-rendered page is
  fully loaded.
- **Raw-HTML CSS cascade approximation accuracy** (already identified and
  accepted by the architect) — acceptable given the documented "Not Available"
  fallback behavior; carry forward into developer guide as a known limitation.
- **Redirect-count verification against Playwright's actual navigation
  behavior** — low-effort verification item for the implementation-planner to
  schedule early (spike/prototype), not a redesign.

---

## Recommendations

### Must Do (for approval)
1. **Define the element-correlation mechanism** used to keep a
   `DiscoveredElement`'s BeautifulSoup node and (when rendered) its
   corresponding Playwright element handle referring to the same DOM node
   across Components 4, 5, and 6. Document the chosen approach (e.g., marker
   attribute injection, or index/XPath-based single lookup) in the
   implementation plan before implementation begins.
2. **Define the concrete size-cap enforcement mechanism for URL-mode
   navigation** (e.g., Playwright `page.route()`/response interception with
   abort-on-threshold) and document it in the implementation plan, rather than
   the current outcome-only description ("streamed byte counting").

### Should Do
1. Spike/verify early in implementation whether Chromium's navigation redirect
   behavior can be counted/capped at exactly 5 hops via Playwright's API, or
   whether an application-level redirect counter needs to be layered on top.
2. Explicitly note the raw-HTML CSS-approximation limitation in the developer
   guide and in the report UI itself (already partially planned via the
   degradation-notice mechanism) so users understand accuracy differs between
   URL/rendered mode and raw-HTML mode.

### Consider for Future
1. Background task queue (Celery/RQ) only if concurrent multi-user usage
   becomes an actual requirement.
2. Containerization (Dockerfile) for onboarding ease, without changing the
   in-process architecture.
3. Optional report persistence/history if users request it (would require
   introducing a database layer and revisiting the "no persistence"
   compliance posture).

---

## Approval Decision

### ⚠️ APPROVED WITH CONDITIONS

- Architecture is sound: component boundaries, technology choices, data flow,
  and diagrams are complete, internally consistent, and fully traceable to the
  approved requirements and acceptance criteria.
- Security is adequate: authentication/authorization omission is justified,
  XSS/TLS/size/information-disclosure controls are concrete and correct, and
  the one accepted risk (SSRF) is a deliberate, documented, requirements-driven
  decision rather than an oversight.
- Scalability/performance approach is adequate and appropriately minimal for
  the stated single-user, local/dev-only MVP scope.
- No critical issues were found that require the solution-architect to revise
  the design's structure.
- **Conditions to be satisfied during Phase 4 (implementation-planner) and
  carried into Phase 5 (implementation-engineer), not requiring re-submission
  to design-reviewer**, unless satisfying them forces a structural change to
  the components or data flow described in `documents/design-document.md`:
  1. Concrete element-correlation mechanism (Must Do #1) must be specified in
     the implementation plan's task breakdown for Components 4–6.
  2. Concrete URL-mode size-cap enforcement mechanism (Must Do #2) must be
     specified in the implementation plan's task breakdown for Component 3.

**Gate status:** Pending coordinator confirmation before
`documents/.approval-gates/03-design-review-approved.txt` is created and
Phase 4 (implementation-planner) begins.

---

**Document Status**: Complete — awaiting coordinator confirmation to proceed
**Reviewed By**: design-reviewer agent
**Next Step (pending confirmation)**: Create approval-gate checkpoint;
implementation-planner begins Phase 4, incorporating the two Must-Do
conditions into its task breakdown.
