# Requirements Specification: Locator Lens

**Story ID**: EPMCDMETST-62704  
**Title**: Locator Lens - Analyze HTML Pages and Generate Locators Report  
**Date**: 2026-08-31  
**Status**: Approved  
**Priority**: Low (Exploratory)

---

## Business Problem

QA Engineers, UI Automation Engineers, and Test Engineers spend significant time manually inspecting web pages, identifying automation locators, and documenting UI element properties. This manual process is:
- Time-consuming and resource-intensive
- Error-prone (inconsistent locator quality)
- Slows down automation script development cycles
- Lacks standardized documentation of element metadata

**Impact**: Reduces productivity in test automation development and increases time-to-delivery for test suites.

---

## Business Objective

Build **Locator Lens**, an internal web application that automates the discovery of UI elements, generation of optimal XPath locators, and extraction of element styling metadata. The tool should enable QA engineers to:
- Rapidly analyze any webpage (via URL or raw HTML)
- Automatically identify interactive and structural elements
- Generate robust, maintainable XPath locators
- Extract computed style information (fonts, colors) for element identification
- View a structured HTML report with all element metadata in a single browser session

**Success Definition**: Engineers can provide a webpage or HTML and receive a production-ready HTML report with XPath locators and element metadata within 30 seconds, eliminating manual inspection time for typical pages.

---

## Target Users

- **QA Engineers**: Automating web application testing
- **UI Automation Engineers**: Building and maintaining test automation frameworks
- **Test Engineers**: Developing test scripts and documenting test data

**User Context**: Internal team only; exploratory tool for dev/QA environment usage.

---

## Functional Requirements

### Requirement 1: URL Input Workflow
- **Description**: System accepts a public webpage URL and analyzes the live page.
- **Details**:
  - User provides URL with http:// or https:// scheme
  - System validates URL format (rejects invalid URLs with clear error message)
  - System follows HTTP redirects (maximum 5 redirects to prevent infinite loops)
  - System enforces TLS certificate validation (rejects invalid/self-signed certs)
  - System applies 30-second timeout for combined fetch + render time
  - System renders JavaScript-rich pages using Playwright (Chromium engine) to capture rendered DOM
  - System extracts and analyzes the rendered DOM structure
- **Priority**: High

### Requirement 2: Raw HTML Input Workflow
- **Description**: System accepts raw HTML content (pasted or uploaded) and analyzes the markup.
- **Details**:
  - User provides HTML as text input or file upload
  - System tolerantly parses HTML, recovering from malformed/incomplete markup (via BeautifulSoup/lxml)
  - Only truly unparseable HTML (e.g., binary data, non-UTF8 content) triggers error rejection
  - System analyzes DOM structure without rendering (no JavaScript execution)
  - System extracts element information from the parsed DOM
- **Priority**: High

### Requirement 3: Element Discovery
- **Description**: System identifies specific UI element types from the analyzed DOM.
- **Details**:
  - Identifies all instances of these 8 element types:
    1. Headings (H1)
    2. Subheadings (H2-H6)
    3. Links (`<a>` elements)
    4. Buttons (`<button>` and `<input type="button">`)
    5. Input fields (`<input>` with all valid types)
    6. Dropdowns (`<select>` controls)
    7. Textareas (`<textarea>` elements)
    8. Clickable role-based elements (e.g., `role="button"`, `role="menuitem"`, `role="tab"`, etc.)
  - **Exclusions**: Does NOT report elements that are:
    - Hidden via CSS (display:none, visibility:hidden, aria-hidden="true")
    - Located inside iframes (both same-domain and cross-domain)
    - Outside the viewport (for MVP simplification)
  - Reports element count and type distribution
- **Priority**: High

### Requirement 4: XPath Locator Generation
- **Description**: System generates optimal XPath locators for each discovered element.
- **Details**:
  - Uses priority-ordered strategy:
    1. **ID-based XPath**: If element has a unique `id` attribute, use `//*[@id='element_id']`
    2. **Unique attribute-based XPath**: If element has unique `name`, `data-testid`, or `aria-label`, use that attribute
    3. **Shortest robust relative XPath**: Use tag + text content and/or position index to create a readable, maintainable path resistant to minor DOM changes
  - When no robust identifier exists, provide best-effort XPath with a note indicating fragility
  - All generated XPaths must be syntactically valid and testable via XPath tools
  - XPath should be as readable as possible (prefer `//*[@id='submit']` over `/html[1]/body[1]/form[1]/button[1]`)
- **Priority**: High

### Requirement 5: Computed Style Metadata Extraction
- **Description**: System extracts CSS styling information for elements with visible text.
- **Details**:
  - Uses `getComputedStyle` (for rendered pages via Playwright) or CSS parsing (for raw HTML) to resolve computed styles
  - Accounts for CSS cascade and inheritance (final rendered values, not just inline styles)
  - Extracts and reports for each element:
    - **Font Family**: Actual computed font family stack
    - **Font Size**: In pixels (e.g., "14px")
    - **Font Color**: In hex RGB format (e.g., "#1a1a1a")
    - **Visible Text**: The actual text content displayed
  - When metadata cannot be extracted or computed: displays "Not Available" (consistent with AC8)
  - Handles edge cases (pseudo-elements, CSS variables, fallback fonts) gracefully
- **Priority**: High

### Requirement 6: HTML Report Generation & Web UI Rendering
- **Description**: System generates a comprehensive HTML report and renders it in the web browser.
- **Details**:
  - Report is generated as HTML and displayed in the user's browser (not downloaded as a file)
  - Report includes:
    - **Project metadata**:
      - Application Name (auto-detected from page `<title>`, URL, or domain; "Not Available" if undetectable)
      - Frontend Technology (auto-detected from meta tags, framework signatures, script sources; "Not Available" if undetectable)
      - Analysis timestamp (date/time analysis was performed)
      - Page source (URL or "Raw HTML")
      - Element summary (total count, breakdown by type)
    - **Element Analysis Table** with columns:
      - Element Name/Text (display text or element identifier)
      - Element Type (Heading, Link, Button, etc.)
      - Tag Name (actual HTML tag)
      - XPath Locator (generated XPath)
      - Font Family (computed, or "Not Available")
      - Font Size (in px, or "Not Available")
      - Font Color (hex, or "Not Available")
      - Relevant HTML Attributes (id, name, class, data-* attrs, aria-* attrs)
    - **Partial failure indicators**: If some elements fail processing, clearly mark them as "Failed" or "Skipped" with reason
  - Report is styled for readability (clean HTML/CSS, print-friendly)
  - Browser support: Modern desktop browsers (Chrome, Firefox, Safari, Edge); Chromium-based preferred
- **Priority**: High

### Requirement 7: Error Handling & Validation
- **Description**: System handles invalid input and errors gracefully with clear user messaging.
- **Details**:
  - **URL validation errors**: Invalid format, unsupported scheme (non-http/https), unreachable domain → displays clear message with guidance
  - **Fetch/render errors**: Network timeout (30s exceeded), TLS validation failure, HTTP error codes → displays message with retry suggestion
  - **HTML parsing errors**: Truly unparseable content (binary, non-UTF8) → displays clear parsing error message; tolerates and recovers from malformed markup
  - **JavaScript render errors**: If Playwright render fails, attempts to parse source HTML instead; reports degradation in report metadata
  - **No elements found**: If analysis discovers zero elements, displays message with diagnostics (page might be iframe-only, JavaScript-generated post-load, etc.)
  - Error messages are actionable (e.g., "Page took >30s to load. Try a simpler page or check network." instead of "Timeout.")
- **Priority**: High

### Requirement 8: Missing Metadata Handling
- **Description**: System consistently indicates unavailable or unextractable data rather than failing or guessing.
- **Details**:
  - Consistent use of "Not Available" placeholder for any metadata that cannot be extracted
  - Examples:
    - Font color for hidden text: "Not Available"
    - Application name when page has no `<title>` or identifiable name: "Not Available"
    - XPath for an unusual/custom element: best-effort XPath with "** Fragile **" note if not robust
  - All "Not Available" indicators are visually consistent in the report
  - User can still see partial results even when some metadata is missing
- **Priority**: Medium

### Requirement 9: Dynamic Page Support
- **Description**: System handles JavaScript-heavy and dynamically rendered pages.
- **Details**:
  - Uses Playwright (Chromium engine) to render pages with JavaScript enabled
  - Waits for common DOM readiness signals (optional, best-effort; apply reasonable wait heuristics)
  - Captures the rendered DOM after JavaScript execution (not the source HTML)
  - Works for modern frameworks: React, Vue, Angular, vanilla JS SPAs
  - Single-threaded MVP: processes one analysis at a time (no concurrent/queued analyses)
  - Does NOT require headless mode optimization (dev-only deployment)
- **Priority**: High

---

## Acceptance Criteria

- [ ] **AC1: URL Input Support** – Given a valid http/https webpage URL with proper format, when submitted, system validates the URL, follows up to 5 redirects, enforces TLS, fetches the page within 30s timeout, renders it with Playwright (Chromium), and extracts the rendered DOM elements for analysis.

- [ ] **AC2: Raw HTML Support** – Given valid or malformed HTML content, when submitted, system tolerantly parses the markup via BeautifulSoup/lxml, recovers from common malformations, and extracts DOM elements without rendering. Only truly unparseable input (binary, non-UTF8) triggers an error.

- [ ] **AC3: Element Discovery** – System identifies all 8 element types (headings, subheadings, links, buttons, inputs, selects, textareas, clickable role-based elements) from the analyzed DOM. Excludes hidden elements (display:none, visibility:hidden, aria-hidden) and all iframe content (both same-domain and cross-domain).

- [ ] **AC4: XPath Generation** – For each discovered element, system generates an ideal XPath using priority order: (1) ID-based, (2) unique attribute-based (name, data-testid, aria-label), (3) shortest robust relative XPath. All XPaths are syntactically valid and testable.

- [ ] **AC5: Style Metadata Extraction** – For elements with visible text, system extracts and reports computed Font Family, Font Size (px), Font Color (hex #RRGGBB), and Visible Text. Uses computed styles to resolve CSS cascade/inheritance. Reports "Not Available" when metadata cannot be extracted.

- [ ] **AC6: HTML Report Generation** – System generates an HTML report and renders it in a web browser containing: auto-detected Application Name and Frontend Technology, analysis timestamp and metadata, a structured element analysis table with all required columns (Name, Type, Tag, XPath, Font Family, Font Size, Color, Attributes), and partial failure indicators if applicable.

- [ ] **AC7: Error Handling** – Invalid input (malformed URLs, unparseable HTML, network/fetch failures, timeouts, TLS errors) produces clear, actionable error messages that guide the user toward resolution (e.g., "Page took >30s to load. Try a simpler page." vs. generic "Timeout").

- [ ] **AC8: Missing Metadata Handling** – Report consistently displays "Not Available" for any metadata that cannot be extracted or computed, ensuring user always sees what succeeded and what could not be determined. No blank cells or missing values cause confusion.

- [ ] **AC9: Dynamic Page Support** – System uses Playwright (Chromium engine) to render JavaScript-heavy pages and analyzes the rendered DOM, supporting modern SPAs (React, Vue, Angular) and vanilla JS. Captures post-JavaScript-execution state within the 30s timeout.

---

## Technical Constraints

| Constraint | Specification |
|-----------|----------------|
| **Backend** | Python (FastAPI or Flask) with Playwright Python bindings for rendering; BeautifulSoup/lxml for HTML parsing and DOM analysis |
| **Frontend** | Lightweight web UI (server-rendered HTML or minimal-JS framework) to display and format the analysis report |
| **Rendering Engine** | Playwright with Chromium engine only (no Firefox, WebKit, or Safari engine) |
| **Max Page Size** | ~5 MB (prevents memory exhaustion; applies to both fetched URLs and uploaded HTML) |
| **Timeout** | ~30 seconds for combined URL fetch + page render (whichever applies) |
| **Concurrency** | Single analysis at a time (no queue, no parallel analyses in MVP) |
| **URL Validation** | Enforce http/https scheme; validate URL format; follow redirects (max 5); enforce TLS certificate validation |
| **Deployment** | Local/dev-only for internal QA team; no production hardening, no CDN, no load balancing required for MVP |
| **Authentication** | None required (trusted internal team) |
| **Authorization** | None required (all authenticated users have full access) |
| **Logging** | Basic console/file logging for debugging; no structured logging or ELK stack required |
| **Database** | None required (stateless MVP; no persistence of analyses) |
| **Browser Support** | Modern desktop browsers (Chrome, Firefox, Safari, Edge); mobile/responsive not required |
| **API** | REST endpoints for URL analysis and HTML analysis; responses return the rendered HTML report (not JSON) |

---

## Constraints & Limitations

### Timeline
- **Priority**: Low (exploratory)
- **Deadline**: None fixed; proceeds at normal SDLC workflow pace
- **Approval Gates**: Must pass requirements, architecture, design review, implementation, code review, and QA before release

### Resource Constraints
- Internal team usage only; no production SLA commitments
- Single-threaded MVP (no concurrency optimization)

### Technical Boundaries (MVP)
- No iframe content analysis (all iframes out of scope)
- No multi-page crawling or site-wide audit
- No screenshot generation or visual regression testing
- No accessibility audits or WCAG scoring
- No authentication/login handling
- No cross-domain restrictions (no allowlist/blocklist)
- No concurrent/async analysis queuing in MVP

---

## Dependencies

**Before implementation can proceed:**
1. Approval of this requirements specification
2. Python development environment with pip package management available
3. Playwright and Chromium browser pre-installed or auto-downloaded by Playwright
4. FastAPI or Flask framework available
5. BeautifulSoup4 and lxml libraries available for parsing
6. Web server/WSGI runner (e.g., uvicorn, gunicorn, flask dev server)

**No external dependencies on other systems** (stateless, no databases, no external APIs required for MVP).

---

## Out of Scope (MVP)

The following features and use cases are **explicitly excluded** from this release:

- **Login-protected pages**: No credential handling, session management, or 2FA support
- **Multi-page crawling**: Single-page analysis only; no "crawl this domain" functionality
- **Screenshot generation**: No visual rendering or image output of analyzed pages
- **Accessibility audits**: No WCAG compliance checking or accessibility scoring
- **Iframe content analysis**: All iframe content (same-domain and cross-domain) is out of scope; iframes are not analyzed or reported
- **Full website audits**: No bulk/batch analysis mode; one page at a time
- **Cross-domain iframe restrictions**: No allowlist/blocklist; users can attempt any URL (note: cross-domain iframes still out of scope)
- **Concurrency & queuing**: No async task queue, no background jobs, no parallel analysis in MVP
- **Mobile/responsive UI**: Report UI is desktop-only; no mobile optimizations
- **Production deployment**: No uptime SLAs, no HA/failover, no CDN, no distributed deployment
- **User authentication**: No login, no roles, no audit trails
- **Persistence**: No database, no history of analyses, no saved reports
- **Advanced XPath generation**: No AI/ML optimization; uses rule-based priority only
- **Browser tabs/windows capture**: Single document analysis only; no tab enumeration

---

## Definition of Done

The story is considered complete when:

**Functional Completion**
- ✓ URL input workflow fully implemented (validation, fetch, render, analysis)
- ✓ Raw HTML input workflow fully implemented (tolerant parsing, analysis)
- ✓ Element discovery working for all 8 element types with proper exclusions (hidden, iframes)
- ✓ XPath generation implemented with priority-order strategy
- ✓ Computed style metadata extraction functional (Font Family, Size, Color, Text)
- ✓ HTML report generation complete with all required metadata and columns
- ✓ Error handling produces clear, actionable messages for all error cases
- ✓ Partial failure handling implemented (skipped items marked in report)
- ✓ Dynamic page support tested with Playwright (Chromium rendering)

**Testing & Quality**
- ✓ Unit tests created with ≥80% code coverage
- ✓ Unit tests verify core logic: URL validation, HTML parsing, element discovery, XPath generation, style extraction
- ✓ Integration tests created using fixture HTML pages or local test server (no live website testing)
- ✓ Integration tests verify end-to-end workflows: URL analysis, HTML analysis, report generation
- ✓ All tests pass consistently (no flakiness)
- ✓ Code passes linting and formatting checks (PEP 8 for Python)
- ✓ No compiler/runtime errors; code runs without exceptions on test suite

**Code & Standards**
- ✓ Code follows project coding standards (see STANDARDS.md)
- ✓ Error handling implemented at all system boundaries
- ✓ No hardcoded secrets or sensitive data in code
- ✓ Input validation at all entry points (URL, HTML, parameters)
- ✓ Security best practices applied (TLS validation, input sanitization)

**Documentation**
- ✓ Inline code comments explain non-obvious logic (why, not what)
- ✓ API documentation includes endpoint specs, request/response examples, error codes
- ✓ Developer guide documents architecture, key design patterns, how to extend
- ✓ Deployment guide describes setup steps, environment config, how to run locally
- ✓ README updated with feature overview and usage instructions

**Review & Approval**
- ✓ Code review completed; all feedback addressed or approved
- ✓ Security scan passes (no critical/high vulnerabilities)
- ✓ QA engineer signs off on functionality and test coverage
- ✓ PR ready for merge to development branch

---

## Stakeholders & Approvers

| Role | Name | Email | Responsibility |
|------|------|-------|-----------------|
| **Reporter** | Vikram Siddavattam | vikram_siddavattam@epam.com | Story author; QA perspective |
| **Product Owner** | [To be assigned] | [To be assigned] | Final approval; user advocacy |
| **Tech Lead** | [To be assigned] | [To be assigned] | Architecture guidance; standards enforcement |
| **Approver** | Project Coordinator | [Provided approval] | Approval gate decision |

---

## Approval & Sign-Off

✅ **Status**: APPROVED  
✅ **Approved by**: Project Coordinator  
✅ **Date**: 2026-08-31  
✅ **Approval Notes**: Consolidated requirements understanding approved with all 15 clarifying questions addressed. Ready for solution-architect phase.

**Next Phase**: Solution Architecture (solution-architect agent)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-08-31 | Requirements Analyst | Initial approved specification |

---

**End of Requirements Specification**
