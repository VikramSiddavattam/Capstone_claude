---
name: architecture-design
description: Transform approved requirements into a scalable, maintainable, secure, and implementable solution architecture. Use for architecture creation and architecture review.
---

# Architecture Design Skill

## Purpose

Transform approved requirements into an architecture that:

- Satisfies functional requirements
- Meets non-functional requirements
- Can be implemented with minimal ambiguity
- Can be operated, monitored, secured, and maintained
- Supports future evolution without unnecessary complexity

This skill defines how architecture work is performed.

---

# When to Use

Use for:

- Producing a new architecture
- Updating an existing architecture
- Reviewing an architecture proposal
- Validating architecture against requirements
- Evaluating architectural risks and trade-offs

---

# Repository First

Before proposing any architecture:

1. Analyze the repository.
2. Identify existing architectural patterns.
3. Identify reusable components.
4. Identify existing technologies in use.
5. Identify platform standards.

Prefer:

- Reuse over replacement
- Consistency over novelty
- Simplicity over complexity

Do not introduce new technologies, frameworks, services, or patterns without documented justification.

---

# Architecture Principles

## Prefer

- Simplicity
- Explicit design decisions
- Secure defaults
- Observable systems
- Proven technologies
- Maintainable solutions
- Requirement-driven decisions
- Monolith-first unless requirements justify distribution

---

## Avoid

- Premature optimization
- Unnecessary microservices
- Technology sprawl
- Over-engineering
- Vendor lock-in without justification
- Clever abstractions that reduce maintainability

---

# Procedure

## 1. Requirements Analysis

Review:

- Functional Requirements
- Non-Functional Requirements
- Constraints
- Dependencies
- Acceptance Criteria

Identify:

- Business drivers
- Technical drivers
- Operational drivers
- Compliance requirements

---

## 2. System Decomposition

Define:

### System Boundaries

What is inside and outside the solution.

### Major Capabilities

Major business and technical capabilities.

### Components

For each component define:

- Purpose
- Responsibilities
- Interfaces
- Dependencies

---

## 3. Architecture Design

Design:

### Component Architecture

How components interact.

### Data Architecture

Define:

- Data ownership
- Data stores
- Data flow
- Data lifecycle
- Consistency model

### Integration Architecture

For each integration define:

- Protocol
- Authentication
- Error handling
- Retry strategy
- Failure behavior

### Deployment Architecture

Define:

- Runtime environment
- Infrastructure model
- Environment strategy
- Deployment approach

---

## 4. Technology Decisions

Only introduce technologies that satisfy documented requirements.

For major decisions document:

### Decision ID

ADR-001

### Context

Problem being solved.

### Options Considered

Reasonable alternatives.

### Decision

Selected approach.

### Rationale

Why it was selected.

### Trade-Offs

Advantages and disadvantages.

### Risks

Known concerns.

### Mitigations

How risks are addressed.

---

## 5. Security Evaluation

Address:

### Authentication

Users and system identities.

### Authorization

Permission enforcement.

### Data Protection

At rest and in transit.

### Secrets Management

Storage and rotation.

### Threat Mitigation

Consider:

- Injection
- Broken access control
- Credential compromise
- Data exposure
- Denial of service
- Misconfiguration

Security requirements must map to architectural controls.

---

## 6. Performance & Scalability

Evaluate:

### Performance

Response times and throughput requirements.

### Compute Scaling

Horizontal and vertical scaling.

### Data Scaling

Replication, partitioning, caching.

### Async Processing

Background processing and messaging.

Design only for documented or reasonably projected scale.

---

## 7. Reliability & Operations

Evaluate:

### Availability

Availability targets.

### Recovery

Backup and restore strategy.

### Failure Handling

Redundancy and resilience.

### Observability

Logs, metrics, traces, alerts.

### Operability

Supportability and troubleshooting requirements.

---

## 8. Risk Assessment

Identify:

- Technical risks
- Security risks
- Operational risks
- Delivery risks

Document:

- Impact
- Probability
- Mitigations

---

## 9. Traceability Check

Verify:

Every requirement maps to:

- One or more architectural elements

Every architectural element maps to:

- One or more requirements

No architecture should exist without business or technical justification.

---

# Architecture Quality Checklist

Before finalizing verify:

## Completeness

- Functional requirements addressed
- Non-functional requirements addressed
- Security addressed
- Operations addressed

## Feasibility

- Architecture is implementable
- Technology choices are realistic
- Team can support the solution

## Maintainability

- Responsibilities are clear
- Complexity is justified
- Dependencies are understood

## Traceability

- Requirements mapped
- Decisions justified
- Risks documented

---

# Outputs

## High-Level Architecture

System overview.

---

## Architecture Drivers

Business and technical drivers.

---

## Component Architecture

Components and interactions.

---

## Data Architecture

Data ownership, flow, storage, and lifecycle.

---

## Integration Architecture

Internal and external integrations.

---

## Security Architecture

Security controls and decisions.

---

## Performance & Scalability

Performance targets and scaling strategy.

---

## Reliability & Operations

Availability, monitoring, resilience, and recovery.

---

## Deployment Architecture

Environments, infrastructure, and deployment strategy.

---

## Architectural Decisions

ADRs and trade-offs.

---

## Risks & Mitigations

Documented architectural risks.

---

## Requirements Traceability

Requirement-to-architecture mapping.

---

# Deliverables

## Authoring

Create:

documents/architecture.md

---

## Review

Create:

documents/architecture-review.md

Review findings should assess:

- Requirement alignment
- Security
- Scalability
- Reliability
- Maintainability
- Complexity
- Risks
- Architectural compliance

---

# Success Criteria

A successful architecture:

- Meets documented requirements
- Has clear component responsibilities
- Has justified technology choices
- Has documented trade-offs
- Is secure by design
- Is operationally supportable
- Is traceable to requirements
- Minimizes unnecessary complexity
