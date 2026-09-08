---
description: Display the current SDLC workflow status based on workflow artifacts and approval checkpoints.
---

Review the following locations:

- documents/
- documents/.approval-gates/

Determine the completion state of each SDLC phase.

# Workflow

1. Requirements Analyst
2. Solution Architect
3. Design Reviewer
4. Implementation Planner
5. Implementation Engineer
6. Code Reviewer
7. Quality Release Engineer
8. PR Generator

# Phase Artifacts

- Requirements Analyst → documents/requirements.md
- Solution Architect → documents/architecture.md
- Design Reviewer → documents/architecture-review.md
- Implementation Planner → documents/implementation-plan.md
- Implementation Engineer → documents/implementation-summary.md
- Code Reviewer → documents/code-review.md
- Quality Release Engineer → documents/qa-report.md
- PR Generator → documents/pull-request.md

# Approval Checkpoints

Located in:

documents/.approval-gates/

Files:

- 01-requirements-approved.txt
- 02-architecture-approved.txt
- 03-design-review-approved.txt
- 04-implementation-plan-approved.txt
- 05-implementation-approved.txt
- 06-code-review-approved.txt
- 07-qa-approved.txt

# Status Rules

✅ Approved

- Approval checkpoint exists

⏳ In Progress

- Artifact exists
- Approval checkpoint does not exist

⏸ Waiting

- Previous phase has not been approved

❌ Rejected

If one of the review artifacts contains:

- REJECTED
- BLOCKED
- NOT READY

Applicable review artifacts:

- architecture-review.md
- code-review.md
- qa-report.md

# Determine

- Status of every workflow phase
- Current active phase
- Most recently approved phase
- Workflow progress
- Blocking condition

# Output

# SDLC Workflow Status

Requirements Analyst
[STATUS]

Solution Architect
[STATUS]

Design Reviewer
[STATUS]

Implementation Planner
[STATUS]

Implementation Engineer
[STATUS]

Code Reviewer
[STATUS]

Quality Release Engineer
[STATUS]

PR Generator
[STATUS]

---

Current Phase:
[Current Active Phase]

Next Action:
[Required Next Step]

Latest Approved Artifact:
[Artifact Name]

Workflow Progress:
[X of 8 phases completed]

Blocked By:
[Missing artifact, approval, or rejection]

Only report workflow state.

Do not:

- Create files
- Modify files
- Approve artifacts
- Reject artifacts
- Advance workflow status
