---
name: review
description: Objective, evidence-based review methodology for architecture and code artifacts. Use for design reviews, implementation reviews, quality assessments, and approval recommendations.
---

# Review Skill

## Purpose

Provide consistent, objective, evidence-based reviews.

The goal of a review is to:

- Validate compliance with requirements
- Identify risks
- Evaluate quality
- Provide actionable feedback
- Support approval decisions

Review against documented requirements and standards, not personal preferences.

---

# When to Use

Use for:

## Architecture Reviews

Review:

- Architecture proposals
- System designs
- Technical designs
- Architecture updates

Typically used by:

- design-reviewer

---

## Code Reviews

Review:

- Implemented code
- Test suites
- Configuration changes
- Supporting implementation artifacts

Typically used by:

- code-reviewer

---

# Review Principles

Every review must be:

## Objective

Findings must be based on evidence.

---

## Traceable

Every finding should reference:

- Requirement
- Design section
- Code file
- Configuration location

as appropriate.

---

## Actionable

Explain:

- What is wrong
- Why it matters
- What should be improved

---

## Risk-Based

Focus on impact and likelihood.

Avoid excessive focus on minor stylistic concerns.

---

## Evidence-Based

Support findings with:

- File references
- Design references
- Requirement references
- Test evidence

Do not rely on assumptions.

---

# Review Procedure

## 1. Establish the Baseline

Review relevant inputs.

For architecture reviews:

- requirements.md
- architecture.md

For code reviews:

- requirements.md
- architecture.md
- implementation-plan.md
- implementation-summary.md

Understand expected behavior before evaluating the artifact.

---

## 2. Evaluate Systematically

Assess the following dimensions where applicable.

### Requirements Coverage

Verify:

- Requirements are addressed
- Acceptance criteria are satisfied
- Scope aligns with approved requirements

---

### Correctness

Verify:

- Behavior matches intent
- Logic appears sound
- Error scenarios are considered

---

### Security

Review:

- Authentication
- Authorization
- Input validation
- Secrets handling
- Data protection
- Access control

---

### Reliability

Review:

- Failure handling
- Recovery strategy
- Resilience
- Operational concerns

---

### Performance & Scalability

Review:

- Performance assumptions
- Resource usage
- Scaling approach
- Potential bottlenecks

---

### Maintainability

Review:

- Clarity
- Separation of concerns
- Modularity
- Testability
- Reusability

---

### Dependency Safety

Review:

- External dependencies
- Technology choices
- Maintenance risks
- Operational risks

---

### Complexity

Identify:

- Duplication
- Over-engineering
- Unnecessary abstractions
- Excessive coupling

---

### Test Coverage

Code Review Only

Review:

- Unit tests
- Integration tests
- Critical path coverage
- Error-path coverage

---

### Architecture Quality

Architecture Review Only

Review:

- Requirement traceability
- Architectural consistency
- Decision rationale
- Technical feasibility

---

## 3. Classify Findings

Every finding must have a severity.

---

### Critical

Must be resolved before approval.

Examples:

- Security vulnerabilities
- Data corruption risk
- Missing core requirements
- Non-implementable architecture
- Broken functionality

---

### High

Should be resolved before approval.

Examples:

- Major architecture concerns
- Significant maintainability issues
- Missing testing on critical paths
- High operational risk

---

### Medium

Important improvement.

Examples:

- Design weaknesses
- Coverage gaps
- Performance concerns

---

### Low

Minor concern.

Examples:

- Small maintainability issues
- Documentation gaps
- Non-blocking improvements

---

### Recommendation

Suggestion only.

No approval impact.

Examples:

- Future enhancement
- Refactoring opportunity
- Documentation improvement

---

# Finding Structure

Every finding should include:

## Title

Concise summary.

---

## Location

Reference:

- File
- Component
- Section
- Requirement

---

## Issue

What is wrong.

---

## Impact

Why it matters.

---

## Recommendation

Suggested corrective action.

Do not rewrite the artifact unless explicitly requested.

---

# Approval Decisions

## APPROVED

No unresolved blocking concerns.

---

## APPROVED WITH COMMENTS

Work may proceed.

Non-blocking findings remain.

---

## APPROVED WITH CONDITIONS

Specific findings must be resolved before the next phase.

---

## BLOCKED

Artifact is not ready to proceed.

Blocking issues exist.

---

# Review Quality Checklist

Before finalizing verify:

## Completeness

- Requirements reviewed
- Risks reviewed
- Security reviewed
- Quality reviewed

---

## Evidence

- Findings reference evidence
- Recommendations are actionable

---

## Consistency

- Severity matches impact
- Same standards applied throughout

---

## Objectivity

- No personal preference findings
- No unsupported claims

---

# Outputs

## Findings

Grouped by severity.

---

## Strengths

Positive observations.

---

## Risks

Documented review risks.

---

## Recommendation

Approval outcome.

---

## Follow-Up Actions

Required next steps.

---

# Deliverables

## Architecture Review

Create:

documents/architecture-review.md

---

## Code Review

Create:

documents/code-review.md

---

# Success Criteria

A successful review:

- Validates compliance
- Identifies meaningful risks
- Provides actionable feedback
- Supports objective decision making
- Documents approval rationale clearly
