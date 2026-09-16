<!-- markdownlint-disable-file -->
---
description: Implementation plan for GitHub issue 2 governed routing, budgets, and policy administration
applyTo: '**'
---

## User Requests

* Read GitHub issue #2 and its full acceptance criteria.
* Research required patterns.
* Plan, implement, and review the result.

## Objectives

Implement issue #2 plus child issues #12, #13, and #14 without weakening the existing
coordinator, replay, retry, or terminal-state invariants.

## Context Summary

Research: `.copilot-tracking/research/2026-09-16/issue-2-economics-policy-research.md`
and its linked subagent report. Applicable instructions cover Python implementation,
pytest conventions, Markdown, and writing style. The `python-foundational` skill applies.

## Implementation Checklist

### Phase 1: Economics Domain

<!-- parallelizable: false -->

* [x] Add immutable policy, eligibility, route decision, reservation, transition, and
  audit contracts.
* [x] Add stable public reason codes and pure versioned route/budget evaluation.
* [x] Validate with a critical direct-route test and a 30-case routing corpus.

### Phase 2: Persistence and Administration

<!-- parallelizable: false -->

* [x] Add policy store, multidimensional budget, and audit protocols.
* [x] Add atomic in-memory adapters and confirmed update/rollback service.
* [x] Validate successful, denied, invalid, stale, and rollback behavior.

### Phase 3: Coordinator Integration

<!-- parallelizable: false -->

* [x] Freeze the active policy and decision in run state.
* [x] Gate admission before paid work and dispatch only the selected alias.
* [x] Reserve each physical model and quality call with typed allowance evidence.
* [x] Validate five over-budget cases and replay compatibility.

### Phase 4: Documentation and Review

<!-- parallelizable: false -->

* [x] Update architecture and public API documentation.
* [x] Run Ruff, focused tests, and the full suite.
* [x] Review every parent and child acceptance criterion.

## Dependencies

* Pydantic immutable contracts
* Existing journal and state transition infrastructure
* Python `Decimal` and lock-protected in-memory adapters
* `python-foundational` skill and repository Python/test instructions

## Success Criteria

All issue #2 and child acceptance criteria have executable coverage. No disallowed paid
path starts, decision evidence is stable and versioned, policy mutations are confirmed
and audited, rollback creates a new immutable version, and all existing tests pass.
