# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project Overview

An **AI-powered SDLC Orchestrator**: a fixed pipeline of specialized agents that turns a business requirement (e.g. a Jira story) into a production-ready solution, with a human approval gate between every phase.

**Key principle**: each phase completes and gets explicit human (or, where noted, agent) approval before the next phase starts. No skipping phases, no parallel phases, no shortcuts.

## Workflow

```
requirements-analyst → solution-architect → design-reviewer → implementation-planner
  → implementation-engineer → code-reviewer → quality-release-engineer → pr-generator
```

Every arrow is an approval gate. See `.claude/rules/approval-gate-rules.md` for the gate process and per-phase approval criteria in full.

| Phase | Agent | Produces | Approval |
|---|---|---|---|
| 1 | requirements-analyst | `documents/requirements.md` | Human |
| 2 | solution-architect | `documents/design-document.md` | Human (via design-reviewer) |
| 3 | design-reviewer | `documents/design-review.md` | Agent decision (APPROVE / REJECT / CONDITIONS) |
| 4 | implementation-planner | `documents/implementation-plan.md` | Human |
| 5 | implementation-engineer | `src/` + `documents/implementation-summary.md` | Human |
| 6 | code-reviewer | `documents/code-review.md` | Agent decision |
| 7 | quality-release-engineer | `documents/qa-report.md` | Human |
| 8 | pr-generator | `documents/pull-request.md` | Final — ready for merge |

Each agent's full responsibilities, process, and output template live in its own definition file under `.claude/agents/`. That file is the source of truth for how that phase works — this document only covers what's shared across phases.

**One artifact per phase.** Every phase writes exactly one consolidated markdown file directly into `documents/` (flat — no per-phase subfolders, no numbered directories). If a phase seems to need multiple documents, put it in one file with multiple sections instead.

On rejection: the reviewer gives specific, actionable feedback; the agent revises and resubmits; repeat until approved. No timeout.

## Agent Execution Rules

Only one phase agent may be active at a time.

An agent may consume:
- prior approved artifacts
- source code
- MCP context

An agent may not:
- modify artifacts owned by another phase
- skip approval gates
- start a downstream phase
  without approval

## Repository Structure

```
.
├── .claude/
│   ├── agents/            # One .md per phase above — each is that agent's full spec
│   ├── hooks/workflow-gates/  # stage-completion.sh, approve-and-transition.sh (standalone scripts;
│   │                          #   not currently wired into settings.json hooks)
│   └── rules/
│       └── approval-gate-rules.md
├── documents/              # One consolidated .md deliverable per phase (see table above)
│   ├── .approval-gates/    # One checkpoint file per completed phase, e.g. 01-requirements-approved.txt
│   └── archive/            # Superseded/historical artifacts
├── src/                     # Production code (implementation-engineer's output)
├── tests/                   # Unit + integration tests (fixtures/local test server, never live sites)
├── README.md
└── CLAUDE.md               # This file
```

Only add a new top-level convention (a new `.claude/` subfolder, a new doc type) when a phase actually needs it — don't pre-create structure for hypothetical future use.

## Available MCP Integrations

### Jira MCP

Used by:
- requirements-analyst

Purpose:
- story retrieval
- bug retrieval
- acceptance criteria extraction

### Knowledge Base MCP

Used by:
- requirements-analyst
- solution-architect

Purpose:
- architectural references
- standards
- reusable guidance

### GitHub MCP

Used by:
- implementation-engineer
- code-reviewer
- pr-generator

Purpose:
- repository analysis
- branch operations
- pull request generation

## Coding Standards

- Static typing where the language supports it; explicit error handling at system boundaries (validate external input, trust internal code).
- Descriptive names; functions < 50 lines; cyclomatic complexity < 10; one responsibility per function.
- Comments explain *why*, never *what* — skip comments where good naming already makes intent obvious.
- No hardcoded secrets; sanitize/validate all external input; parameterized queries.
- Follow the language's own convention (PEP 8 for Python, etc.); consistent formatting via the project's linter/formatter once one is configured.

## Testing Standards

- **Coverage**: ≥80% overall; 100% on auth/payment/security-critical paths.
- **Types**: unit (isolated, mocked dependencies, milliseconds), integration (real component interaction, fixtures/local test server), end-to-end (full workflow), performance (when the story has explicit perf requirements).
- Every new feature ships with tests; every fixed bug gets a regression test.
- One behavior per test, named for what it verifies; tests are independent and order-agnostic; no flaky tests — fix the root cause or remove it.
- Integration/E2E tests use fixtures or a local test server — never real live websites/services, for determinism.

## Working in This Repo

- Read the relevant `.claude/agents/*.md` file before acting as that phase — it's the authoritative process for that stage, not this file.
- Don't do more than one phase's work in a turn, and don't create a phase's approval-gate checkpoint file until the human (or, for design-reviewer/code-reviewer, the agent itself per the table above) has actually signed off.
- Keep `documents/` flat and one-file-per-phase; keep this file itself lean — add project-specific facts here, not generic software-engineering advice available anywhere else.

---

**Last Updated**: 2026-09-01
