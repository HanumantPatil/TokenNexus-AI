<!-- markdownlint-disable-file -->

---
description: Implement GitHub issue 1 governed request orchestration
applyTo: '**'
---

# Issue 1 Governed Orchestration Plan

## User Requests

* Read GitHub issue #1 and its full acceptance criteria.
* Research the required implementation patterns.
* Plan the implementation.
* Build the implementation.
* Review the completed result.

## Objectives

* Deliver child issue #9 strict versioned request and result contracts.
* Deliver child issue #10 deterministic coordination and scoped idempotency.
* Deliver child issue #11 provider-neutral model ports and deterministic substitutes.
* Prove the epic's replay-safe terminal outcomes and coordinator-only transition authority.

## Context Summary

The repository is requirements-first and has no application stack. Prior research
selects an application-owned coordinator, RFC 8785 fingerprints, UUIDv7 identifiers,
RFC 9457 errors, canonical decimal strings, and deterministic substitutes. Python 3.11+
is selected for the first executable slice and uses the repository-root `.venv-x64`.

Applicable guidance includes the Markdown, writing style, prompt builder, Python,
Python test, uv project, and Python foundational standards loaded during research.

## Implementation Checklist

### Phase 1: Project and Contracts

<!-- parallelizable: false -->

* [x] Add a locked Python project configuration and package layout.
* [x] Implement strict request, result, money, quality, usage, and problem contracts.
* [x] Implement UUIDv7 generation, normalization, RFC 8785 fingerprints, and reasons.
* [x] Add contract and fingerprint tests.

### Phase 2: State, Journal, and Coordinator

<!-- parallelizable: false -->

* [x] Implement immutable run state and terminal-state rules.
* [x] Implement scoped atomic idempotency claims and stored terminal replay.
* [x] Implement reservation-before-dispatch, cancellation, deadline, retry, and escalation gates.
* [x] Add orchestration tests with exact call-count assertions.

### Phase 3: Provider-Neutral Adapters

<!-- parallelizable: false -->

* [x] Implement model and quality protocols.
* [x] Implement deterministic scripted substitutes with no hidden retries.
* [x] Add adapter parity and repeatability tests.

### Phase 4: Documentation and Review

<!-- parallelizable: false -->

* [x] Document package usage and architecture without overwriting unrelated README changes.
* [x] Run Ruff, pytest, and package build validation.
* [x] Review every issue criterion against executable evidence.

## Dependencies

* Python 3.11+
* Pydantic 2.x for strict immutable boundary models and Draft 2020-12 schemas
* rfc8785 for canonical JSON serialization
* uuid6 for UUIDv7 on Python versions without `uuid.uuid7`
* pytest and Ruff for validation
* Python foundational skill and repository Python instructions

## Success Criteria

* Valid requests normalize and receive UUIDv7 request IDs.
* Invalid requests produce field-specific RFC 9457 problem details before execution.
* Canonical fingerprints and scoped idempotency enforce replay and conflict behavior.
* All request paths terminate once and terminal results cannot be mutated.
* No test observes more than two quality attempts, one escalation, or one transient retry.
* Both model aliases satisfy one contract and scripted calls remain exact and repeatable.
* Ruff, pytest, and package build validation pass.
