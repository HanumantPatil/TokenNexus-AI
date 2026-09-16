<!-- markdownlint-disable-file -->

# Issue 1 Governed Orchestration Details

## Context

* Plan: .copilot-tracking/plans/2026-09-16/issue-1-governed-orchestration-plan.instructions.md
* Research: .copilot-tracking/research/2026-09-16/issue-1-governed-orchestration-research.md
* Subagent research: .copilot-tracking/research/subagents/2026-09-16/issue-1-governed-orchestration-research.md

## Phase 1 Details

Create `src/tokennexus` with strict frozen Pydantic models. Reject unknown fields,
validate canonical decimals and supported contract versions, export Draft 2020-12
schemas, and map validation failures to safe RFC 9457 problem details. Fingerprint the
normalized request projection with RFC 8785 and SHA-256. Exclude generated and mutable
execution fields from the projection.

Success requires tests for defaults, unknown fields, invalid constraints, UUIDv7,
property-order-independent fingerprints, semantic fingerprint changes, and closed
reason-code validation.

## Phase 2 Details

Create immutable run and attempt records plus an in-memory journal implementing atomic
scope-and-key claims. The coordinator claims admission before effects, reserves the
estimated cost before every model call, checks cancellation and the absolute deadline,
and commits the first terminal outcome. Replays return journaled state; conflicts do
not invoke dependencies.

Success requires routine, escalation, retry, replay, conflict, cancellation, timeout,
budget denial, and terminal immutability tests with exact provider call counts.

## Phase 3 Details

Define narrow model and evaluator protocols using TokenNexus contracts only. Scripted
substitutes return fixed outcomes or typed failures and append one call record per
invocation. They never retry or select a route. Coordinator policy selects
`economical` first and `capable` only for one approved quality escalation.

Success requires alias parity, one-call-per-invocation behavior, and identical repeated
runs under deterministic clocks and IDs.

## Phase 4 Details

Add focused developer documentation outside the user-modified README. Validate with
Ruff, pytest, and a package build. Review the implementation against issue #1 and all
three child issues, then record validation and any scoped deferrals.
