---
name: requirements-analysis
description: Transform business needs, user stories, feature requests, Jira work items, and supporting documentation into complete, traceable, testable software requirements and acceptance criteria.
---

# Requirements Analysis Skill

## Purpose

Transform business requests and supporting documentation into:

- Clear requirements
- Testable acceptance criteria
- Documented assumptions
- Traceable specifications

This skill defines how requirements analysis is performed.

---

# Source Authority Order

When multiple sources exist, use the following order of precedence:

1. Supplied attachments
2. Approved business documentation
3. Jira issues
4. Knowledge base / Confluence references

Lower-priority sources must not override higher-priority sources without explicit documentation.

If conflicts exist:

- Document the conflict.
- Identify affected requirements.
- Record required resolution.
- Do not silently merge contradictory statements.

---

# Analysis Procedure

## 1. Collect Sources

Gather and review all available sources.

Possible inputs include:

- Attachments
- Jira issues
- User stories
- Feature requests
- Business requirement documents
- Knowledge base articles
- Confluence pages
- Existing specifications

Record all source identifiers.

---

## 2. Discover Context

Identify:

- Business goals
- Business outcomes
- Stakeholders
- User groups
- Success measures
- Expected behaviors

Document why the capability is needed.

---

## 3. Reconcile Sources

Compare all collected sources.

Identify:

- Conflicts
- Gaps
- Duplicates
- Missing dependencies

Do not invent resolutions.

Document unresolved conflicts explicitly.

---

## 4. Classify Findings

Organize information into:

### Functional Requirements

System behaviors.

### Non-Functional Requirements

Quality attributes.

Examples:

- Performance
- Scalability
- Reliability
- Security
- Availability
- Compliance

### Constraints

Restrictions that impact implementation.

### Dependencies

Internal and external dependencies.

### Assumptions

Temporary working assumptions.

### Open Questions

Information required before implementation.

---

## 5. Gap Analysis

Identify:

- Missing requirements
- Ambiguous wording
- Undefined business rules
- Missing acceptance criteria
- Missing dependencies
- Missing success measures

Generate clarification questions.

Never fill gaps through speculation.

---

## 6. Validation

Verify that requirements are:

- Complete
- Consistent
- Testable
- Traceable
- Understandable
- Non-contradictory

Flag anything that prevents validation.

---

## 7. Acceptance Criteria Definition

Create measurable acceptance criteria.

Every requirement should have supporting validation criteria.

Prefer objective pass/fail outcomes.

When appropriate use:

```text
Given
When
Then
```

format.

---

## 8. Traceability

Trace every requirement back to one or more sources.

Maintain the relationship between:

```text
Source
    -> Requirement
        -> Acceptance Criteria
```

No requirement should exist without a source reference.

---

# Requirement Quality Standards

Every requirement must be:

## Clear

A reader can understand the intent.

## Atomic

Represents one requirement.

## Testable

Can be objectively verified.

## Measurable

Has observable success criteria.

## Traceable

Can be linked to its source.

## Unambiguous

Has one reasonable interpretation.

---

# Requirement Identification

Assign identifiers.

## Functional Requirements

```text
FR-001
FR-002
FR-003
```

---

## Non-Functional Requirements

```text
NFR-PERF-001
NFR-SEC-001
NFR-REL-001
NFR-OPS-001
```

---

## Acceptance Criteria

```text
AC-001
AC-002
AC-003
```

---

# Assumptions

Assumptions are temporary working statements.

Example:

```text
ASSUMPTION-001

Email delivery service will be available.
```

Assumptions are not requirements.

---

# Gaps

Gaps are missing information that prevents complete definition.

Example:

```text
GAP-001

Password complexity requirements not defined.
```

Gaps require clarification.

---

# Source Conflicts

Document conflicts explicitly.

Example:

```text
CONFLICT-001

Jira states:
Session timeout = 15 minutes

Attachment states:
Session timeout = 30 minutes

Resolution Required:
Business owner decision.
```

---

# Deliverable Structure

## Source References

List all analyzed sources.

---

## Business Context

### Business Goals

### Stakeholders

### User Groups

---

## Functional Requirements

### FR-001

Description

Source References

---

## Non-Functional Requirements

### NFR-SEC-001

Description

Source References

---

## Constraints

---

## Dependencies

---

## Assumptions

---

## Open Questions

---

## Acceptance Criteria

### AC-001

Pass/Fail Criteria

---

## Source Conflicts

---

## Traceability Matrix

| Requirement | Acceptance Criteria | Source |
|------------|---------------------|---------|
| FR-001 | AC-001 | Jira-123 |
| FR-002 | AC-002 | BRD-2.1 |

---

# Outputs

Produce:

- Source References
- Business Context
- Functional Requirements
- Non-Functional Requirements
- Constraints
- Dependencies
- Assumptions
- Open Questions
- Acceptance Criteria
- Source Conflicts
- Traceability Matrix

---

# Deliverable

Create:

documents/requirements.md

---

# Success Criteria

A successful requirements analysis results in:

- Complete requirement coverage
- Testable acceptance criteria
- Documented assumptions
- Documented conflicts
- Clear traceability
- No hidden ambiguity
- No invented scope
