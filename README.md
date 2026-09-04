# SDLC Orchestrator - AI-Powered Workflow Automation

Transform business requirements into production-ready solutions through an 8-phase AI-orchestrated workflow with human approval gates.

## Quick Start

### 1. Open Workspace

```bash
code Capstone_claude.code-workspace
```

### 2. Set Environment Variables

```bash
export JIRA_BASE_URL=https://jiraeu.epam.com/
export JIRA_EMAIL=your-email@example.com
export JIRA_API_TOKEN=your-api-token
```

Or create `.env` file in project root:

```
JIRA_BASE_URL=https://jiraeu.epam.com/
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
```

### 3. Start Workflow

Run any phase command from VS Code Command Palette:
- `SDLC: Phase 1: Requirements Analyst`
- `SDLC: Phase 2: Solution Architect`
- etc.

Or start requirements analyst agent with your user story.

## 8-Phase Workflow

```
User Story
    ↓
[1] requirements-analyst → ⏸️ APPROVE/REJECT
    ↓
[2] solution-architect → ⏸️ DESIGN REVIEW
    ↓
[3] design-reviewer (approve/reject)
    ↓
[4] implementation-planner → ⏸️ APPROVE/REJECT
    ↓
[5] implementation-engineer → ⏸️ CODE REVIEW
    ↓
[6] code-reviewer (approve/reject)
    ↓
[7] quality-release-engineer → ⏸️ APPROVE/REJECT
    ↓
[8] pr-generator
    ↓
🚀 READY FOR PRODUCTION
```

## Project Structure

```
.
├── .vscode/                    # VS Code configuration
│   ├── settings.json          # Workspace settings
│   ├── tasks.json             # Workflow phase tasks
│   ├── launch.json            # Debug configurations
│   ├── extensions.json        # Recommended extensions
│   └── keybindings.json       # Custom key bindings
├── .claude/                   # Claude Code configuration
│   ├── settings.json          # MCP & workflow config
│   ├── agents/
│   │   ├── agent-manifest.json
│   │   ├── requirements-analyst.md
│   │   ├── solution-architect.md
│   │   └── ... (all 8 agents)
│   ├── commands/
│   │   └── commands-manifest.json
│   ├── hooks/
│   │   └── hooks-manifest.json
│   └── rules/
│       └── rules-manifest.json
├── documents/                 # Workflow artifacts (flat, no per-phase subfolders)
│   ├── requirements.md
│   ├── design-document.md
│   ├── design-review.md
│   ├── impl-plan.md
│   ├── implementation-summary.md
│   ├── code-review.md
│   ├── qa-report.md
│   ├── pull-request.md
│   └── .approval-gates/
├── src/                       # Production source code
├── tests/                     # Test suites
├── mcp-servers/               # MCP servers
│   └── jira-server/          # Jira integration
├── Capstone_claude.code-workspace
├── CLAUDE.md                  # Claude Code guidance
├── WORKFLOW.md               # Workflow documentation
└── README.md                 # This file
```

## Key Commands

### From Command Palette (Ctrl+Shift+P)

```
SDLC: Phase 1: Requirements Analyst
SDLC: Phase 2: Solution Architect
...
SDLC: Phase 8: PR Generator
SDLC: Approve Current Phase
SDLC: Reject Current Phase
SDLC: Show Workflow Status
SDLC: Sync with Jira
```

### From Terminal

```bash
# Run phase task
code-run-task "Phase 1: Requirements Analyst"

# Start Jira MCP server
python mcp-servers/jira-server/server.py

# Check workflow status
ls documents/.approval-gates/
```

## Workflow Features

✅ **Sequential**: Each phase completes before next begins
✅ **No Skipping**: All 8 phases required in order
✅ **Human Controlled**: Approval gates at critical phases
✅ **Traceable**: Full audit trail in `documents/.approval-gates/`
✅ **Documented**: All artifacts organized by phase
✅ **Integrated**: Jira synchronization available

## Approval Gates

| Phase | Approval Type | Gate |
|-------|--------------|------|
| 1 | Human | requirements-analyst output |
| 2 | Human | solution-architect output |
| 3 | Automated | design-reviewer output |
| 4 | Human | implementation-planner output |
| 5 | Human | implementation-engineer output |
| 6 | Automated | code-reviewer output |
| 7 | Human | qa-release-engineer output |
| 8 | Final | pr-generator output |

## Rules & Standards

- **Code**: PEP 8, <50 line functions, cyclomatic complexity <10, 80%+ test coverage
- **Documentation**: Markdown in phase directories
- **Security**: No critical/high vulnerabilities
- **Sequencing**: No parallel work, strict phase order
- **Rejection**: Iterate until approved, no timeout

## Jira Integration

Optional Jira integration for workflow tracking:

```bash
# Start Jira MCP server
cd mcp-servers/jira-server
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python server.py
```

Then use Jira tools in Claude sessions to track workflow in Jira.

## VS Code Extensions

Recommended extensions (auto-installed from `.vscode/extensions.json`):
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Prettier (esbenp.prettier-vscode)
- GitLens (eamodio.gitlens)
- Markdown (yzhang.markdown-all-in-one)

## Configuration Files

- **`.vscode/settings.json`** - Editor and Python settings
- **`.vscode/tasks.json`** - Phase tasks
- **`.vscode/launch.json`** - Debug configs
- **`.claude/settings.json`** - MCP and workflow config
- **`.claude/agents/agent-manifest.json`** - Agent definitions
- **`.claude/commands/commands-manifest.json`** - Commands
- **`.claude/hooks/hooks-manifest.json`** - Event hooks
- **`.claude/rules/rules-manifest.json`** - Enforcement rules

## Next Steps

1. Open workspace: `code Capstone_claude.code-workspace`
2. Set environment variables (Jira credentials)
3. Invoke first phase: `SDLC: Phase 1: Requirements Analyst`
4. Provide user story when prompted
5. Review output in `documents/requirements.md`
6. Approve or reject in VS Code
7. Next phase automatically starts on approval

## Documentation

- **CLAUDE.md** - Claude Code operating guide
- **WORKFLOW.md** - Detailed workflow process
- **DEVELOPMENT.md** - Development setup and commands
- **STANDARDS.md** - Coding and testing standards

## For More Information

See individual phase agent files in `.claude/agents/` for specific responsibilities and requirements for each phase.

---

## Locator Lens (Story EPMCDMETST-62704)

**Locator Lens** is the application produced by this SDLC workflow instance: an
internal, local/dev-only tool that analyzes a webpage (URL or raw HTML),
discovers UI elements (headings, links, buttons, inputs, dropdowns, textareas,
and clickable role-based elements), generates prioritized XPath locators,
extracts computed style metadata (font family/size/color, visible text), and
renders the results as an HTML report directly in the browser.

### Setup

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

(Or simply `make setup`.)

### Run

```bash
cd src
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open `http://127.0.0.1:8000/` in a browser, submit a URL or paste raw
HTML, and view the generated report. `GET /health` returns a liveness check;
`GET /docs` serves the auto-generated OpenAPI/Swagger documentation.

### Test

```bash
make test              # full suite
make test-unit         # unit tests only
make test-integration  # integration tests only (fixture pages + local
                        # HTTP server; no live-website testing)
make test-coverage     # pytest-cov report
```

Source: `src/app/`. Tests: `tests/unit/`, `tests/integration/`,
`tests/fixtures/`. Implementation details, test coverage, and key decisions
are documented in `documents/implementation-summary.md`.
