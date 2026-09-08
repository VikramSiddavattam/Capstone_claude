---
name: pr-generator
description: Consolidate approved SDLC artifacts into a final pull request package. Produce pull-request.md with business context, implementation summary, validation results, release notes, deployment guidance, and merge readiness assessment. After human approval, raise the actual GitHub PR with labels.
tools: [Read, Write, Edit, Glob, Grep, Bash, mcp__github__get_me, mcp__github__create_pull_request, mcp__github__list_pull_requests, mcp__github__update_pull_request, mcp__github__issue_write, mcp__github__list_branches, mcp__github__get_file_contents, mcp__github__search_pull_requests, mcp__github__list_commits, mcp__github__push_files, mcp__github__get_label]
model: haiku
---

# PR Generator

## Purpose

Create the final delivery package for reviewers, approvers, and release teams.

Consolidate all approved SDLC artifacts into a single pull request document that tells the complete story from business need through implementation and validation.

You are responsible for release documentation and delivery readiness reporting.

You must not:

- Modify source code
- Change requirements
- Change architecture
- Change implementation decisions
- Modify review outcomes
- Modify QA outcomes
- Create approval gates
- Approve deployment or merge

---

## Scope

Only raise a PR for **current existing changes** — the files modified, added, or staged on the current branch relative to `main`. Do not re-document the entire project history on every invocation.

Determine the scope by running:

```bash
git diff main...HEAD --name-only
git status --short
```

The PR covers only what those commands report. If there are no changes, STOP and report that there is nothing to raise a PR for.

---

## Gate Check

Before beginning verify:

- documents/requirements.md exists
- documents/design-document.md exists
- documents/implementation-plan.md exists
- documents/implementation-summary.md exists
- documents/code-review.md exists
- documents/qa-report.md exists

If any required artifact is missing:

STOP.

Do not generate PR documentation.

---

## Inputs

Required:

- documents/requirements.md
- documents/design-document.md
- documents/implementation-plan.md
- documents/implementation-summary.md
- documents/code-review.md
- documents/qa-report.md
- `git diff main...HEAD` output (scope of current changes)

---

## Responsibilities

### Executive Summary

Summarize:

- Business problem
- Business value
- Delivered solution
- Release recommendation

---

### Delivery Summary

Document:

- Features implemented
- Scope delivered
- Acceptance criteria status
- Out-of-scope items

---

### Technical Summary

Summarize:

- Solution architecture
- Significant implementation decisions
- Major technical outcomes

---

### Quality Summary

Summarize:

- Code review outcome
- Testing outcome
- Security validation
- Performance validation
- QA recommendation

---

### Release Information

Prepare:

- Release notes
- Deployment guidance
- Rollback guidance
- Operational considerations

---

### Risk Summary

Document:

- Known limitations
- Accepted risks
- Open issues
- Planned follow-up actions

Maintain complete transparency.

---

### Traceability

Provide references to:

- Requirements
- Architecture
- Planning
- Implementation
- Code Review
- QA Validation

Maintain end-to-end lifecycle traceability.

---

### Merge Readiness Assessment

Provide:

- Readiness status
- Outstanding concerns
- Preconditions
- Final recommendation

---

## Deliverable

Append the generated PR documentation to **this file** (`.claude/agents/pr-generator.md`) under a new dated section heading at the bottom:

```
---

## PR — <YYYY-MM-DD> — <branch-name>

<full PR documentation here>
```

Do **not** write a separate `documents/pull-request.md`. Each run appends a new dated section; do not overwrite or remove previous entries.

---

## Pull Request Structure

# Pull Request

## Metadata

### Labels

Required Labels:

- ai-generated
- claude

---

## Executive Summary

- What changed
- Why it matters
- Merge recommendation

---

## Business Context

- Problem addressed
- Business goals
- User impact

---

## Scope Delivered

- Features implemented
- Acceptance criteria coverage
- Out-of-scope items

---

## Technical Summary

- Architecture summary
- Technical decisions
- Implementation highlights

---

## Quality Summary

- Review outcome
- Test results
- Security validation
- Performance validation

---

## Known Risks & Limitations

- Known issues
- Accepted risks
- Mitigations
- Follow-up actions

---

## Release Notes

User-facing release summary.

---

## Deployment Guidance

Deployment considerations and references.

---

## Rollback Guidance

Rollback considerations and references.

---

## Monitoring Considerations

- Important metrics
- Operational watch areas
- Post-release validation focus

---

## Artifact Traceability

Reference all SDLC artifacts.

---

## Merge Readiness Assessment

- READY FOR MERGE
- CONDITIONAL
- NOT READY

Include rationale.

---

## Documentation Standards

The pull request must be:

- Accurate
- Concise
- Traceable
- Actionable
- Honest

Summarize information.

Do not duplicate entire source documents.

Reference source artifacts whenever possible.

---

## Quality Checklist

Before completion verify:

### Coverage

- Requirements represented
- Design represented
- Implementation represented
- Review represented
- QA represented

### Accuracy

- Results match source artifacts
- Findings match review outputs
- Recommendations match QA outputs

### Traceability

- Requirements linked
- Design linked
- Implementation linked
- Validation linked

### Release Readiness

- Deployment guidance documented
- Rollback guidance documented
- Risks documented
- Recommendation documented

---

## Artifact Ownership

Owns:

- `.claude/agents/pr-generator.md` (appends PR documentation sections here)

Must not modify:

- requirements.md
- design-document.md
- implementation-plan.md
- implementation-summary.md
- code-review.md
- qa-report.md
- documents/pull-request.md (do not create or modify this file)

---

## Exit Criteria

This phase is complete when:

- A new dated PR section has been appended to `.claude/agents/pr-generator.md`
- The section covers only the current branch changes
- All relevant SDLC phases are summarized
- Risks are documented
- Release recommendation is documented
- Traceability is complete

---

## Approval Gate

Submit the pull request package for human review.

Do not create approval checkpoint files.

Merge approval is a human decision.

---

## GitHub PR Creation (After Human Approval)

Use **MCP tools exclusively** — do not use `gh` CLI. MCP tools are reliable and atomic; `gh` CLI commands can fail silently.

### Step 1: Ensure the branch is pushed

```bash
git push -u origin <current-branch>
```

### Step 2: Create the PR via MCP

Call `mcp__github__create_pull_request` with:
- `owner`: repo owner (from `mcp__github__get_me`)
- `repo`: repo name
- `title`: from the Metadata section of the PR document
- `body`: full PR document content
- `head`: current branch name
- `base`: `main`

### Step 3: Ensure required labels exist in the repo

For each required label (`ai-generated`, `claude`), call `mcp__github__get_label`:
- If the label does **not** exist, create it via `mcp__github__issue_write` is not suitable for label creation — use `Bash` as a fallback only for this step:

```bash
gh label create "ai-generated" --color "0075ca" --description "Generated by AI" --repo <owner>/<repo> 2>/dev/null || true
gh label create "claude" --color "7057ff" --description "Generated by Claude" --repo <owner>/<repo> 2>/dev/null || true
```

### Step 4: Add labels to the PR — MANDATORY

Call `mcp__github__issue_write` with `method: "update"`:
- `owner`: repo owner
- `repo`: repo name
- `issue_number`: the PR number returned in Step 2
- `labels`: `["ai-generated", "claude"]`

This step is **not optional**. The PR must have both labels applied before reporting completion.

### Step 5: Verify labels applied

After Step 4, confirm the PR has the labels by checking the response from `mcp__github__issue_write`. Report the final PR URL and confirm labels are applied.

Required labels:
- `ai-generated`
- `claude`

Labels must appear in the PR's Labels field — not in the PR body/description.

---

## Memory

Read `.claude/memory/MEMORY.md` before starting. After raising the PR, update `.claude/memory/` for any new preferences or decisions expressed during this session. See CLAUDE.md `## Project Memory` for the full update process.

---

## Key Behaviors

1. Tell the complete delivery story.
2. Maintain end-to-end traceability.
3. Be transparent about risks.
4. Summarize rather than duplicate.
5. Optimize for reviewer efficiency.
6. Produce user-focused release notes.
7. Present objective merge readiness information.
8. Always create a **new** PR for each run — never update an existing PR unless the user explicitly requests it.

---

## Metadata Requirements

Every generated PR must include:

### Workflow Metadata

- Workflow Type: AI-Assisted SDLC
- Platform: Claude Code
- Generated By: Claude Code Agents

### Required Labels

- ai-generated
- claude

---

**Output:** Appended section in `.claude/agents/pr-generator.md`

**Final Phase:** Human Review & Merge Approval

---

## PR — 2026-09-08 — feature/initial-implementation

# Pull Request

## Metadata

**Title**: feat: implement Locator Lens - AI-powered HTML locator analysis tool
**Branch**: `feature/initial-implementation` → `main`
**Story ID**: EPMCDMETST-62704
**Date**: 2026-09-08
**Workflow Type**: AI-Assisted SDLC
**Platform**: Claude Code
**Generated By**: Claude Code Agents (pr-generator)

### Labels

- ai-generated
- claude

---

## Executive Summary

**What changed**: This PR delivers the full implementation of Locator Lens, a new internal web application that automates the discovery of UI elements, generation of XPath locators, and extraction of element style metadata from web pages or raw HTML. The feature branch adds 70+ files spanning application source code, a complete test suite, configuration, and all SDLC documentation artifacts.

**Why it matters**: QA and automation engineers spend significant manual time inspecting web pages and documenting locators for test scripts. Locator Lens eliminates that manual work by producing a structured, browser-rendered report in under 30 seconds — directly reducing test automation development overhead.

**Merge recommendation**: READY FOR MERGE. All seven SDLC phases are complete and approved. The implementation passed 104/104 tests with 95% code coverage (threshold: 80%), zero lint findings, a full security review with no critical/high issues, and an independent live end-to-end verification by the quality-release-engineer agent.

---

## Business Context

**Problem addressed**: Manual web-page inspection for locator generation is time-consuming, error-prone, and slows test automation delivery. Teams lacked a standardized, automatable way to inventory interactive elements and their metadata.

**Business goals**:
- Enable QA engineers to analyze any webpage (URL or raw HTML) and receive a production-ready XPath locator report in ≤30 seconds
- Eliminate inconsistent, ad-hoc manual locator documentation
- Provide computed style metadata (font family, size, color) alongside structural locators for richer element identification

**User impact**: Internal QA/automation engineers get an on-demand web tool: paste a URL or HTML, click Analyze, receive a downloadable-quality HTML report with per-element XPath and style data. No manual DOM inspection required.

---

## Scope Delivered

### Features Implemented

1. **URL input workflow** — URL validation (http/https only), Playwright/Chromium rendering with 30s timeout, up to 5 redirects, TLS enforcement, ~5MB size cap via `page.route()` interception, and render-failure fallback to raw HTTP fetch.
2. **Raw HTML input workflow** — Tolerant BeautifulSoup/lxml parsing; recovers from malformed markup; ~5MB cap on upload/paste.
3. **Element discovery** — All 8 target element types (H1, H2–H6, `<a>`, buttons, inputs, selects, textareas, ARIA role-based clickables); exclusion of hidden elements (including ancestor-propagation), all iframe content, and viewport-outside elements.
4. **XPath generation** — Three-tier priority strategy: ID-based → unique attribute (name/data-testid/aria-label) → text/position fallback with fragility tagging; every XPath validated via `lxml.etree.XPath()`.
5. **Computed style extraction** — `getComputedStyle` via live Playwright handle (URL mode); CSS simple-selector cascade approximation via `tinycss2` (raw HTML mode); hex-normalized font color, family, size, visible text.
6. **HTML report** — Browser-rendered Jinja2 report with auto-detected application name and frontend technology, analysis timestamp, 8-column element table, "Not Available"/"** Fragile **"/"Failed" consistent labeling, XSS-safe via Jinja2 autoescaping.
7. **Error handling** — Actionable, typed error messages for all failure modes (invalid URL, TLS failure, timeout, oversized page, unparseable HTML, no elements found, analysis lock busy).
8. **FastAPI application** — `GET /`, `POST /analyze`, `GET /health`, `GET /docs`, `GET /openapi.json`; sync routes in thread pool; single-analysis threading lock.

### Acceptance Criteria Coverage

| Criterion | Status |
|---|---|
| AC1: URL input support | Delivered |
| AC2: Raw HTML support | Delivered |
| AC3: Element discovery (8 types, exclusions) | Delivered |
| AC4: XPath generation (priority order, syntactically valid) | Delivered |
| AC5: Style metadata extraction | Delivered |
| AC6: HTML report (all required columns) | Delivered |
| AC7: Error handling (actionable messages) | Delivered |
| AC8: Missing metadata ("Not Available" consistently) | Delivered |
| AC9: Dynamic page support (Playwright/Chromium) | Delivered |

### Out-of-Scope Items (confirmed excluded per requirements)

Login-protected pages, multi-page crawling, screenshot generation, accessibility auditing, iframe content analysis, concurrent/queued analysis, mobile UI, production deployment, persistence/history, AI/ML-based XPath optimization.

---

## Technical Summary

**Architecture**: Single-tier Python web application using FastAPI (server-rendered HTML responses, not a SPA). A five-stage pipeline processes each request: Input Acquisition → Element Discovery → XPath Generation → Style Extraction → Report Assembly. Playwright/Chromium handles URL rendering; BeautifulSoup/lxml handles all DOM parsing.

**Key technical decisions**:
- Sync route handlers with Starlette's thread-pool delegation (simpler than bridging sync Playwright API into async event loop)
- `data-ll-idx` marker-injection correlation scheme (Must-Do #1) — injected into live DOM, used for O(1) live-handle lookup, stripped from report output
- `page.route()` document-level size interception (Must-Do #2) — enforces ~5MB cap before oversized response reaches the browser engine
- Dataclasses for internal pipeline objects (non-serializable BS4/Playwright references); Pydantic only at FastAPI request boundary
- Single-pass, priority-ordered element classification to avoid duplicate rows for elements matching multiple type selectors
- Hidden-ancestor propagation in static analysis (visible child inside `display:none` parent correctly excluded)

**Implementation highlights**:
- 15 Python source modules + 4 Jinja2 templates under `src/app/`
- Typed exception hierarchy with actionable `.message` on every error type
- `aria-hidden` explicitly checked in both rendered and static modes (Playwright `is_visible()` does not account for it)
- Color normalization handles `#rgb`, `#rrggbb`, `rgb()`/`rgba()`, common named colors; returns "Not Available" rather than guessing

---

## Quality Summary

**Code review outcome**: APPROVED (Phase 6, `documents/code-review.md`). Independent line-by-line review of every pipeline module, routes, models, templates, and representative test files. Both Must-Do mechanisms verified correct. No CRITICAL or MAJOR findings. Three MINOR non-blocking observations recorded.

**Test results**:
- 104/104 tests passed (verified independently across Phases 5, 6, and 7 — no flakiness)
- 95% overall code coverage (threshold: 80%)
- Critical-path modules (validation, parsing, discovery, XPath, style): 92–100% each
- 78 unit tests + 26 integration tests; integration suite uses fixture HTML and a local `http.server` + real Playwright/Chromium (never live public websites)

**Lint/formatting**: `flake8 src/app` (max-line-length 100) — zero findings. PEP 8 compliant.

**Security validation**:
- XSS: Jinja2 `select_autoescape(["html"])` active; no `|safe` filter usage anywhere in templates
- TLS: never disabled in either Playwright or httpx fallback paths
- URL scheme: restricted to http/https; `file://`, `javascript:` etc. rejected at input boundary
- Size bounding: ~5MB enforced on both URL (route interception) and raw HTML (pre-decode length check) paths
- Stack-trace leakage: unexpected exceptions logged server-side, generic safe message returned to client
- File upload: client-supplied filename used only as display label, never as a filesystem path
- No hardcoded secrets; no auth surface; no database
- SSRF: not mitigated beyond redirect cap and 30s timeout — an accepted architectural risk for this internal trusted-network MVP, already disclosed and approved in the design review

**Performance validation**: No performance regressions. XPath uniqueness checks are O(n) per element — acceptable for the documented ~5MB/few-thousand-elements envelope. Single-analysis lock prevents concurrent load. 30s timeout bounds worst-case latency.

**QA recommendation**: READY FOR RELEASE (Phase 7, `documents/qa-report.md`). All Definition-of-Done items satisfied. App starts cleanly, `/health` responds, `/analyze` end-to-end verified live.

---

## Known Risks & Limitations

### Accepted Risks (carried forward from architecture, approved in design review)

| Risk | Accepted Mitigation |
|---|---|
| SSRF: users can submit internal/loopback URLs | Redirect cap (5), 30s timeout; internal trusted-network deployment only |
| Raw-HTML style extraction is narrow (simple selectors only) | "Not Available" returned rather than guessing; per-spec honesty preference |
| URL-mode TLS failures briefly misclassified as RenderError before resolving via fallback (MINOR-2) | End-user outcome is still a TLS error message; cosmetic/non-functional only |

### Open Minor Observations (non-blocking, optional post-release)

1. **MINOR-1**: `tech_detect.py` at 86% coverage — script-`src` framework-detection branches untested. Safe fallback to "Not Available" already in place.
2. **MINOR-2**: TLS failures during URL-mode document fetch trigger a fallback round-trip and a slightly misleading "Degraded analysis" notice (see Risk above).
3. **MINOR-3**: `logging_config.py` file-handler-failure path (lines 22, 38–41) not exercised — sandboxed CI limitation; defensive code for unlikely filesystem-permission scenario.

### Known MVP Limitations (by design)

Single-analysis-at-a-time (no queue); no persistence; no iframe analysis; no login/auth; no mobile UI; local/dev-only deployment.

---

## Release Notes

**Locator Lens v1.0 (MVP)**

New internal web tool for QA and automation engineers.

**What's new**:
- Analyze any public webpage by URL or paste raw HTML — no manual DOM inspection required
- Automatic discovery of all interactive and structural elements (headings, links, buttons, inputs, dropdowns, textareas, ARIA clickables)
- XPath locators generated per best-practice priority strategy (ID → unique attribute → text/position)
- Computed style metadata (font family, size, color) extracted and displayed per element
- Browser-rendered HTML report with application name, technology, timestamp, and full element table
- Clear, actionable error messages for invalid input or network failures

**How to use**: Start the application locally (see Deployment Guidance), open `http://127.0.0.1:8000/`, provide a URL or paste HTML, and click Analyze.

**Limitations**: Single-page, single-user, local/dev deployment only. No login-protected pages, no iframe analysis, no concurrent sessions.

---

## Deployment Guidance

This is a local/dev-only MVP — no staging or production tier required.

```bash
# 1. Checkout this branch / pull the merged commit
git checkout main   # after merge

# 2. Create and activate a Python virtual environment
python -m venv .venv
.venv/Scripts/activate   # Windows; source .venv/bin/activate on *nix

# 3. Install dependencies (pinned in requirements.txt)
pip install -r requirements.txt
playwright install chromium

# 4. (Recommended) Verify with the test suite
pytest --cov=src/app -q   # should report 104 passed, 95% coverage

# 5. Start the application
cd src
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. Smoke check
curl http://127.0.0.1:8000/health   # expect {"status":"ok"}
```

`make setup`, `make test`, `make run` targets in the `Makefile` wrap the same steps.

No environment variables, secrets, external services, or database setup are required.

---

## Rollback Guidance

Given the stateless, no-database, local-only nature of this MVP:

1. Stop the running `uvicorn` process (`Ctrl+C` or kill by PID).
2. Check out the previous known-good commit: `git checkout <previous-commit-sha>`
3. Re-sync dependencies if `requirements.txt` changed: `pip install -r requirements.txt`
4. If the Playwright Chromium pin changed: `playwright install chromium`
5. Restart and verify via `GET /health` and a sample `/analyze` request.

No data migration, no database reconciliation, and no persisted analysis history to handle.

---

## Monitoring Considerations

This MVP is a local developer tool with no production monitoring infrastructure. Post-deployment validation focus:

- `GET /health` → `{"status":"ok"}` confirms the process is up
- `GET /docs` → Swagger UI confirms FastAPI is serving correctly
- `POST /analyze` with a known HTML snippet → compare element count and sample XPath to expected (use the snippet from `documents/qa-report.md` Section 4 as a quick sanity check)
- Watch application logs (`logs/` directory) for any unexpected exceptions during use
- If URL-mode analyses consistently degrade to "static HTML fallback", verify Playwright/Chromium installation is intact (`playwright install chromium`)

---

## Artifact Traceability

| Phase | Artifact | Status |
|---|---|---|
| 1 — Requirements | `documents/requirements.md` | Approved 2026-08-31 |
| 2 — Architecture | `documents/design-document.md` | Approved |
| 3 — Design Review | `documents/design-review.md` | APPROVED |
| 4 — Implementation Plan | `documents/impl-plan.md` | Approved |
| 5 — Implementation | `documents/implementation-summary.md` + `src/` + `tests/` | Approved |
| 6 — Code Review | `documents/code-review.md` | APPROVED |
| 7 — QA Report | `documents/qa-report.md` | Approved |
| — | `documents/.approval-gates/01-requirements-approved.txt` through `07-qa-testing-approved.txt` | All present |

---

## Merge Readiness Assessment

### Status: READY FOR MERGE

**Rationale**:

- All 9 functional requirements implemented; all 9 acceptance criteria satisfied
- 104/104 tests pass; 95% overall code coverage (threshold 80%); zero lint findings
- Full security review: no critical or high-severity issues; all mitigations verified in code
- Independent live end-to-end verification performed by quality-release-engineer agent
- Both design-review Must-Do mechanisms (element correlation, URL-mode size cap) verified correct by code-reviewer and live-verified by quality-release-engineer
- All seven SDLC phases completed with explicit approval gates; all seven approval-gate checkpoint files present
- Three minor, non-blocking observations documented; none warrant rework before merge

**Outstanding concerns**: None that block merge. The three MINOR observations (tech-detect coverage gap, cosmetic TLS misclassification, logging defensive branch) are recorded above as optional post-release follow-up items.

**Preconditions for merge**: Human reviewer approves this PR documentation and confirms the GitHub PR is raised.

**Final recommendation**: Approve and merge to `main`.

---

## PR — 2026-09-08 — feature/initial-implementation (Customization Fixes)

# Pull Request

## Metadata

**Title**: fix: update Claude Code agent definitions and configuration
**Branch**: `feature/initial-implementation` → `main`
**Date**: 2026-09-08
**Workflow Type**: Claude Code Configuration Maintenance
**Generated By**: Claude Code Agents (pr-generator)

### Labels

- ai-generated
- claude

---

## Executive Summary

**What changed**: This PR applies a suite of targeted fixes to Claude Code agent specifications, SDLC documentation templates, MCP configuration, and IDE settings to ensure consistency across all phases and eliminate stale references.

**Why it matters**: Consistent artifact naming and correct tool references are foundational to the SDLC orchestrator workflow. Stale configuration that references non-existent Claude Code event types or incorrect MCP methods can cause confusion during phase transitions and prevent proper tooling integration.

**Merge recommendation**: READY FOR MERGE. These are non-functional configuration and documentation corrections. All changes are confined to agent spec files, rules, and configuration — no source code or business logic affected. No tests required.

---

## Business Context

**Problem addressed**: During agent definition review, several naming inconsistencies and stale references were identified:
- Artifact filenames referenced in agent specs did not match actual filenames in `documents/`
- An obsolete hooks manifest referenced fictional Claude Code event types with zero effect
- MCP tool reference was stale in requirements-analyst agent
- IDE settings included Copilot-specific configuration unrelated to Claude Code

**Business goals**:
- Ensure all agent definitions reference correct artifact filenames
- Remove fictional/non-functional configuration
- Correct all MCP tool references for accuracy
- Streamline IDE configuration to remove tooling noise

**User impact**: Internal developers/agents working with this repository will see consistent, accurate references to artifacts and tools, eliminating potential confusion during workflow transitions.

---

## Scope Delivered

### Changes Made

1. **Artifact filename consistency** (C1, C2):
   - Updated all agent bodies to reference `documents/design-document.md` (formerly `architecture.md`)
   - Updated all agent bodies to reference `documents/design-review.md` (formerly `architecture-review.md`)
   - Updated `CLAUDE.md` and `approval-gate-rules.md` to reference `documents/implementation-plan.md` (formerly `impl-plan.md`)

2. **MCP tool reference correction** (M1):
   - Fixed stale MCP tool name in `requirements-analyst.md`
   - Changed `mcp_atlassian_mcp_jira_get_issue` → `mcp__jira__jira_get_issue`

3. **Non-functional configuration removal** (m1, m2):
   - Deleted `.claude/hooks/hooks-manifest.json` (contained fictional Claude Code event types: `workflow:start`, `gate:approved`)
   - Removed `"chat.promptFilesRecommendations"` from `.vscode/settings.json` (Copilot-specific setting)

### Files Modified

- `.claude/agents/code-reviewer.md` — artifact filename updates
- `.claude/agents/design-reviewer.md` — artifact filename updates
- `.claude/agents/implementation-engineer.md` — artifact filename updates
- `.claude/agents/implementation-planner.md` — artifact filename updates
- `.claude/agents/pr-generator.md` — artifact filename updates
- `.claude/agents/quality-release-engineer.md` — artifact filename updates
- `.claude/agents/requirements-analyst.md` — artifact filename + MCP tool reference updates
- `.claude/agents/solution-architect.md` — artifact filename updates
- `.claude/commands/phase-status.md` — artifact filename updates
- `.claude/hooks/hooks-manifest.json` — **deleted**
- `.claude/rules/approval-gate-rules.md` — artifact filename updates
- `.vscode/settings.json` — removed Copilot setting
- `CLAUDE.md` — artifact filename updates

### Scope Verification

No source code changes. No test changes. No business logic modifications. Configuration and documentation only. All changes are backward-compatible with existing workflows; they simply correct references to match actual file paths and tool names.

---

## Technical Summary

**Change type**: Pure configuration and documentation correction.

**Key fixes**:
- Naming consistency: all agent specs now reference the actual filenames in `documents/`
- Tool accuracy: MCP tool reference now uses the correct public method name per MCP server
- Configuration hygiene: removed non-existent event types and IDE-tool-specific settings that have no effect on Claude Code

**Implementation approach**: Systematic find-and-replace across agent definitions, rules, and supporting docs. Single pass; no functional logic changes.

---

## Quality Summary

**Testing**: No functional changes; no tests required. Changes are pure configuration and documentation.

**Validation**: Manual verification of:
- All agent files updated consistently for artifact filename changes
- MCP tool reference corrected to match server capability
- Deleted files confirmed non-functional (hooks-manifest.json contained only stale fictional event types)
- Copilot setting removal confirmed harmless (Copilot not used in this Claude Code workflow)

**Lint/format**: Existing markdown/YAML formatting preserved throughout.

**No regressions**: These are additive corrections (fixing stale references). No prior workflows are disrupted; references are now accurate.

---

## Known Risks & Limitations

None. These are corrections to documentation and configuration only. No functional risk.

---

## Release Notes

**Claude Code Agent Definitions — Configuration Fix**

Updated agent specifications and SDLC documentation for consistency and accuracy.

**What's fixed**:
- Agent definitions now reference correct artifact filenames (`design-document.md`, `design-review.md`, `implementation-plan.md`)
- MCP tool reference in requirements-analyst updated to correct public method name
- Removed non-functional hooks manifest (contained fictional event types)
- Removed Copilot-specific IDE setting

**No user-facing impact**: Internal configuration updates; no change to workflow or functionality.

---

## Deployment Guidance

No deployment required. These are agent specification updates confined to configuration and documentation.

If you are using this SDLC orchestrator:
1. Pull the updated branch
2. No dependencies to install; no configuration scripts to run
3. Agent workflows will now reference correct artifact filenames automatically

---

## Rollback Guidance

If needed, revert to prior commit:

```bash
git revert <commit-sha>
```

This will restore former artifact filename references. No data migration or state reconciliation needed.

---

## Monitoring Considerations

Not applicable (configuration-only change). No runtime monitoring needed.

---

## Artifact Traceability

This PR contains corrections to agent definitions themselves. No changes to business requirements, design, implementation, or validation artifacts.

| Artifact | Impact |
|---|---|
| `.claude/agents/` files | Updated artifact filename references for consistency |
| `CLAUDE.md` | Updated artifact filename in workflow table |
| `.claude/rules/approval-gate-rules.md` | Updated artifact filename in output locations table |
| `.vscode/settings.json` | Removed Copilot-specific setting |
| `.claude/hooks/hooks-manifest.json` | Deleted (non-functional) |

---

## Merge Readiness Assessment

### Status: READY FOR MERGE

**Rationale**:

- All changes are configuration and documentation corrections only; no functional code modified
- Artifact filename updates align references across all agent definitions
- MCP tool reference corrected to match actual server capability
- Stale/non-functional configuration removed
- No source code, no tests, no business logic affected
- No regressions; changes are fixes to existing inaccuracies

**Outstanding concerns**: None.

**Preconditions for merge**: Human reviewer confirms changes are as intended.

**Final recommendation**: Approve and merge to `main`.

---

## PR — 2026-09-08 — feature/initial-implementation (Memory System)

# Pull Request

## Metadata

**Title**: docs: add project memory system to CLAUDE.md and pr-generator
**Branch**: `feature/initial-implementation` → `main`
**Date**: 2026-09-08
**Workflow Type**: Documentation & Configuration
**Generated By**: Claude Code Agents (pr-generator)

### Labels

- ai-generated
- claude

---

## Executive Summary

**What changed**: This PR establishes a project-scoped memory system for storing and sharing agent preferences, decisions, and feedback. It adds `.claude/memory/` directory with an index and migrates the pr-generator feedback (always create new PR) to local project storage, integrated into CLAUDE.md and the pr-generator agent spec.

**Why it matters**: Agents should not rely solely on global Claude profile knowledge. Project-specific preferences, user feedback, and architectural decisions need to be stored in version control within the repository for consistency and transparency across all team members and future agent invocations.

**Merge recommendation**: READY FOR MERGE. This is a foundational configuration change enabling better agent collaboration and decision traceability. No source code affected; purely organizational improvement.

---

## Business Context

**Problem addressed**: Agent decisions and user preferences were previously stored only in global Claude profile memory, which is invisible to repository history and cannot be shared reliably across team members or across agent invocations in different contexts.

**Business goals**:
- Establish a shared, version-controlled memory system for project decisions
- Provide clear process for agents to read and contribute feedback
- Make project preferences transparent and auditable in the repository
- Enable consistent, repeatable behavior across all agents and sessions

**User impact**: Internal developers and agents working with this repository now have a clear, searchable record of all project decisions, preferences, and feedback — all versioned alongside the code.

---

## Scope Delivered

### Changes Made

1. **Add project memory directory** (`.claude/memory/`):
   - New `MEMORY.md` index file — lists all recorded project memories with one-line pointers
   - New `feedback_pr_always_new.md` — migrated feedback: "always create new PR for each commit batch"

2. **Update CLAUDE.md**:
   - Add `.claude/memory/` and `.claude/skills/` to repo structure diagram
   - Add new `## Project Memory` section explaining the memory system
   - Document memory types (feedback, project, user, reference)
   - Provide clear process for agents to create/update memory entries

3. **Update pr-generator agent spec**:
   - Add `## Memory` section reminding agent to read `.claude/memory/MEMORY.md`
   - Add instruction to update memory after PR if new preferences emerge
   - Add Key Behavior #8: "Always create a new PR for each run — never update existing PR unless explicitly requested" (migrated from global memory)

### Quality & Testing

- No functional changes; pure documentation and configuration
- Backward-compatible; all prior workflows unaffected
- Memory system is opt-in for agents during their work phases

---

## Technical Summary

**Change type**: Documentation and configuration enhancement.

**Structure**:
- `.claude/memory/MEMORY.md` — Index file; one-liner per memory entry with link
- `.claude/memory/<slug>.md` — Individual memory entries with YAML frontmatter (name, description, type) and body (rule + why + how)
- All updated references in CLAUDE.md and pr-generator.md to tie agents into the system

**Design decisions**:
- Memory files live in version control (not external storage) for transparency and auditability
- Frontmatter pattern matches existing agent spec conventions for consistency
- Index file acts as quick reference; agents navigate via index rather than directory listing
- Memory types (feedback, project, user, reference) allow semantic categorization for future search/filtering

---

## Quality Summary

**Testing**: Not applicable (documentation-only change).

**Validation**: Manual review of:
- Memory index links to correct files
- Frontmatter syntax correct in both memory files
- CLAUDE.md tree diagram matches actual filesystem
- All cross-references consistent (pr-generator.md references CLAUDE.md correctly)

**Lint/format**: Markdown formatting follows existing project conventions.

**No regressions**: This is purely additive. No existing workflows, agents, or processes are disrupted. Agents are not forced to use the memory system during initial rollout; it becomes a best practice over time.

---

## Known Risks & Limitations

None. This is a foundational organizational change with no operational risk.

---

## Release Notes

**Project Memory System v1.0**

Establish a project-scoped memory system for recording and sharing agent preferences and decisions.

**What's new**:
- `.claude/memory/` directory for project-wide decisions and feedback
- MEMORY.md index — quick reference to all recorded project memories
- Process for agents to read/write project preferences without relying on global profile knowledge
- Integration point for all SDLC agents to contribute and consume shared project knowledge

**For agents**: Read `.claude/memory/MEMORY.md` at the start of your phase. If you learn a new user preference or project constraint during your work, record it following the frontmatter + body template in CLAUDE.md `## Project Memory`.

---

## Deployment Guidance

No deployment required. This is a repository-level organizational change.

To adopt:
1. Pull this branch
2. All agents will automatically read from `.claude/memory/MEMORY.md` when invoked
3. Memory files are now part of the repository history and visible to all team members

---

## Rollback Guidance

If needed, revert this commit:

```bash
git revert <commit-sha>
```

This will remove `.claude/memory/` and revert CLAUDE.md / pr-generator.md changes. Agents will revert to prior memory behavior.

---

## Monitoring Considerations

Not applicable (configuration-only change). No runtime or deployment monitoring needed.

---

## Artifact Traceability

This PR modifies foundational agent configuration:

| Artifact | Changes |
|---|---|
| `CLAUDE.md` | Added `.claude/memory/` to repo structure; added Project Memory section |
| `.claude/agents/pr-generator.md` | Added Memory section; added Key Behavior #8 |
| `.claude/memory/MEMORY.md` | New file: index for all project memories |
| `.claude/memory/feedback_pr_always_new.md` | New file: migrated pr-generator feedback |

---

## Merge Readiness Assessment

### Status: READY FOR MERGE

**Rationale**:

- Changes are organizational improvements to agent coordination, not functional code
- Memory system follows established patterns (YAML frontmatter, markdown body) consistent with agent specs
- Process is clearly documented in CLAUDE.md for all agents to follow
- Foundational for future agent improvements and feedback integration
- No breaking changes; backward-compatible

**Outstanding concerns**: None.

**Preconditions for merge**: Human reviewer confirms the memory system structure and process are acceptable.

**Final recommendation**: Approve and merge to `main`.
