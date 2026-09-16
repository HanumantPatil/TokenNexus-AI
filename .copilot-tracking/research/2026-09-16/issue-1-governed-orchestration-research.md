<!-- markdownlint-disable-file -->

# Issue 1 Governed Orchestration Research

## Scope

Implement GitHub epic #1 and its P0 children #9, #10, and #11 as the first executable
TokenNexus core. The implementation must prove strict contracts, deterministic
coordination, replay safety, bounded work, and provider-neutral model behavior without
requiring Azure connectivity.

## Evidence

* GitHub issue #1 and child issues #9, #10, and #11
* docs/prds/tokennexus-ai-framework-prd.md
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/domain-contracts-reason-codes-research.md
* .copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md
* .copilot-tracking/research/subagents/2026-09-16/issue-1-governed-orchestration-research.md

## Selected Approach

Create a Python 3.11+ package with strict Pydantic contracts, RFC 8785 request
fingerprints, UUIDv7 identifiers, a closed dotted reason-code registry, a coordinator
that alone owns transitions, an idempotency journal port, and scripted model and
quality substitutes. Use immutable domain records and injected clocks and ID sources
so repeated tests produce stable outcomes and exact call counts.

Keep provider SDKs, HTTP hosting, semantic cache, live quality evaluation, and Azure
infrastructure outside this epic. Their ports are defined here, but adding unresolved
integrations would weaken rather than prove the epic's deterministic boundaries.

## Required Invariants

* Exact replay returns the original in-progress or terminal outcome without new work.
* Key reuse with a different canonical fingerprint conflicts before execution.
* Every paid dispatch follows a budget reservation.
* A request has at most two quality attempts, one escalation, and one transient retry.
* Cancellation, deadline expiry, and terminal states prevent all later transitions.
* Model results report facts; only the coordinator chooses retry, escalation, or final status.
* Both model aliases and deterministic substitutes use the same provider-neutral contract.
* Public outcomes contain only registered dotted reason codes and safe messages.

## Validation Strategy

Use focused pytest suites for contracts, fingerprints, coordinator paths, replay,
conflicts, cancellation, timeouts, retries, escalation bounds, terminal immutability,
adapter parity, and deterministic repetition. Run Ruff and the complete test suite from
the repository-root `.venv-x64` environment.
