<!-- markdownlint-disable-file -->
---
title: Issue 2 Economics Policy Implementation Details
description: Phase-level operations and validation for the issue 2 plan
ms.date: 2026-09-16
ms.topic: reference
---

## Context

Plan: `.copilot-tracking/plans/2026-09-16/issue-2-economics-policy-plan.instructions.md`

Research: `.copilot-tracking/research/2026-09-16/issue-2-economics-policy-research.md`

## Phase Details

1. Extend contracts and reasons, then implement `policy.py` as a pure evaluator. The
   first discriminating check is a critical request that must choose `capable`.
2. Implement policy history and audit as one lock-protected transaction. Implement a
   reservation ledger that checks money, token, time, and tool ceilings atomically.
3. Add frozen policy and route decision fields to run state. Integrate coordinator
   admission and typed reservations while retaining default constructor behavior.
4. Update package exports and architecture docs. Validate focused suites before Ruff
   and the complete test suite.

## Acceptance Mapping

* Issue #12: policy evaluator corpus and coordinator direct-route tests
* Issue #13: over-budget matrix, typed reservation ordering, and atomic ledger tests
* Issue #14: administration update, denial, validation, stale version, and rollback tests
* Issue #2: coordinator result evidence and no-disallowed-dispatch assertions
