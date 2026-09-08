---
name: verification
description: Confirm implemented functionality satisfies requirements and acceptance criteria using test execution results, traceable evidence, and documented review outcomes. Use before declaring work complete or preparing release documentation.
---

# Verification Skill

## Purpose

Verify that implemented functionality satisfies approved requirements.

Verification must be based on evidence.

Never assume:

- Code works because it compiles
- Tests pass because they passed previously
- Requirements are implemented because code exists
- Review findings are resolved without verification

Evidence is required.

---

# When to Use

Use for:

## Implementation Validation

Verify implementation before handoff to review.

Typically used by:

- implementation-engineer

---

## Release Validation

Verify the solution before release readiness assessment.

Typically used by:

- quality-release-engineer

---

## Evidence Collection

Gather verification evidence for release and PR documentation.

Typically used by:

- pr-generator

---

# Verification Principles

## Evidence First

Every claim must reference evidence.

Examples:

- Test result
- File location
- Coverage report
- Requirement mapping
- Review outcome

---

## Requirement-Based

Verification begins with requirements.

Do not verify implementation in isolation.

Verify implementation against:

- Functional requirements
- Non-functional requirements
- Acceptance criteria

---

## Traceable

Every acceptance criterion should map to:

```text
Requirement
    -> Implementation
        -> Test
            -> Verification Result
```

---

## Reproducible

Verification should be repeatable by another reviewer.

---

# Verification Procedure

## 1. Establish Baseline

Review:

- documents/requirements.md
- documents/architecture.md
- documents/implementation-summary.md

If available:

- documents/code-review.md
- documents/architecture-review.md

Understand expected behavior before verification.

---

## 2. Requirement Verification

For each requirement:

Verify:

- Requirement implementation exists
- Corresponding behavior exists
- Acceptance criteria can be validated

Document:

- PASS
- FAIL
- PARTIAL

Every requirement should have evidence.

---

## 3. Acceptance Criteria Traceability

Map every acceptance criterion to:

- Implementation location
- Test location
- Verification evidence

Example:

```text
AC-001
Implementation:
src/auth/login.py

Test:
tests/test_login.py::test_successful_login

Status:
PASS
```

---

## 4. Test Execution

Run automated tests.

Do not assume tests pass.

Review:

- Unit tests
- Integration tests
- End-to-end tests
- Smoke tests (if present)

Capture:

- Number executed
- Pass count
- Fail count
- Skipped tests

---

## 5. Coverage Validation

Identify:

### Covered Requirements

Requirements with automated validation.

### Partially Covered Requirements

Requirements requiring additional validation.

### Uncovered Requirements

Requirements with no verification evidence.

Flag all coverage gaps.

---

## 6. Documentation Verification

Verify documentation aligns with implementation.

Review:

- requirements.md
- architecture.md
- implementation-summary.md

Identify:

- Missing updates
- Stale documentation
- Contradictions

---

## 7. Review Closure Verification

Review findings from:

- architecture-review.md
- code-review.md

Verify findings are:

- Resolved
- Accepted
- Deferred

Document unresolved items.

Do not assume findings are closed.

---

## 8. Known Limitation Review

Verify documented limitations.

Determine:

- Risk level
- User impact
- Acceptance status

Document unresolved risks.

---

# Verification Status Definitions

## PASS

Requirement fully implemented and verified.

Evidence exists.

---

## FAIL

Requirement not implemented or verification failed.

Evidence exists.

---

## PARTIAL

Requirement partially implemented or partially verified.

Additional work required.

---

## NOT VERIFIED

Insufficient evidence exists.

Verification cannot be completed.

---

# Verification Quality Checklist

Before finalizing verify:

## Requirements

- All requirements reviewed
- All acceptance criteria reviewed

---

## Testing

- Test suite executed
- Failures documented
- Coverage gaps documented

---

## Traceability

- Requirement mapping exists
- Test mapping exists
- Evidence documented

---

## Reviews

- Review findings checked
- Closure status documented

---

## Documentation

- Documentation matches implementation

---

# Outputs

## Requirement Traceability Matrix

| Requirement | Acceptance Criteria | Test Evidence | Status |
|------------|--------------------|---------------|--------|

---

## Test Execution Summary

Document:

- Tests executed
- Results
- Failures
- Skipped tests

---

## Coverage Gaps

Requirements lacking verification evidence.

---

## Review Closure Status

Outstanding findings and dispositions.

---

## Known Limitations

Outstanding accepted limitations.

---

## Verification Summary

Overall verification result.

---

# Deliverable

Create:

documents/verification-report.md

---

# Verification Decision

Determine one of:

## VERIFIED

Requirements implemented and validated.

---

## VERIFIED WITH GAPS

Implementation functions but gaps remain.

Document gaps explicitly.

---

## NOT VERIFIED

Requirements cannot be validated.

Verification failed.

---

# Success Criteria

A successful verification:

- Validates all requirements
- Verifies acceptance criteria
- Executes tests
- Documents evidence
- Identifies coverage gaps
- Confirms review closure
- Produces an auditable validation trail
