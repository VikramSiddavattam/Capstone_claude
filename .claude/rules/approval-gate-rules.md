# Approval Gate Rules

Sequential workflow with human approval gates between phases.

## Workflow Phases

1. **requirements-analyst** → Creates requirements
2. ⏸️ **HUMAN APPROVAL REQUIRED** 
3. **solution-architect** → Creates architecture design
4. ⏸️ **HUMAN APPROVAL REQUIRED** (design-reviewer)
5. **implementation-planner** → Creates implementation plan
6. ⏸️ **HUMAN APPROVAL REQUIRED** 
7. **implementation-engineer** → Writes code
8. ⏸️ **HUMAN APPROVAL REQUIRED** (code-reviewer)
9. **quality-release-engineer** → Runs tests and validates
10. ⏸️ **HUMAN APPROVAL REQUIRED** 
11. **pr-generator** → Prepares release

## No Skipping

Each phase must complete before next begins. No parallel work.

## Approval Process

1. **Agent completes work** → Produces deliverables directly in `documents/`
2. **Human reviews** → Examines output against approval criteria
3. **Decision**:
   - ✅ **APPROVED** → Next agent starts
   - ❌ **REJECTED** → Agent revises and resubmits

## Output Locations

All stage deliverables are written directly under `documents/` (flat, no per-phase subfolders):

```
documents/
├── requirements.md           → requirements-analyst output (single consolidated file)
├── design-document.md        → solution-architect output (single consolidated file: architecture, diagrams, tech rationale, security)
├── design-review.md          → design-reviewer output (single consolidated file)
├── implementation-plan.md    → implementation-planner output (single consolidated file)
├── implementation-summary.md → implementation-engineer output (single consolidated file; code itself lives in src/)
├── code-review.md            → code-reviewer output (single consolidated file)
├── qa-report.md               → quality-release-engineer output (single consolidated file)
├── pull-request.md           → pr-generator output (single consolidated file)
└── .approval-gates/          → per-phase approval checkpoints
```

## Approval Criteria by Phase

### Phase 1: Requirements
✓ Requirements clear and unambiguous
✓ Acceptance criteria measurable and testable
✓ Scope clearly bounded

### Phase 2: Architecture Design
✓ Architecture aligns with requirements
✓ Technology choices justified
✓ Scalability and security addressed

### Phase 3: Design Review
✓ Architecture feasible
✓ No critical security issues
✓ Performance achievable

### Phase 4: Implementation Plan
✓ Work breakdown complete
✓ Dependencies mapped
✓ Effort estimates realistic

### Phase 5: Implementation
✓ All features implemented
✓ Unit tests ≥80% coverage
✓ Code follows standards

### Phase 6: Code Review
✓ Code review passed
✓ Security scan cleared
✓ Test coverage adequate

### Phase 7: QA Testing
✓ All tests pass
✓ Performance meets requirements
✓ Release checklist verified

## Rejection Handling

If any phase is rejected:
1. Reviewer provides specific feedback
2. Previous agent revises based on feedback
3. Resubmit for approval (repeat until approved)

No timeout - iterate until approved.
