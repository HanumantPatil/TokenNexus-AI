<!-- markdownlint-disable-file -->
---
title: Issue 2 Economics Policy Research
description: Consolidated research for governed routing, budgets, and policy administration
ms.date: 2026-09-16
ms.topic: concept
---

## Scope and Success Criteria

Implement GitHub issue #2 and child issues #12 through #14. Admission must freeze an
immutable policy, select the lowest-cost eligible funded alias, record stable decision
evidence, reserve all declared allowance dimensions before paid work, and support
audited confirmed policy updates and rollback.

## Evidence

* The current coordinator always begins with `economical`, so critical requests cannot
  route directly to `capable`.
* The current budget protocol reserves money only and returns a Boolean without an
  immutable receipt.
* Public decisions omit policy and pricing versions, pre-execution estimate, budget
  action, and eligibility gates.
* No policy store or administration service exists.
* Existing journal and state transitions already provide immutable, compare-and-set
  request execution and should remain the orchestration authority.

Detailed evidence and the acceptance test matrix are recorded in
`../subagents/2026-09-16/issue-2-economics-policy-research.md`.

## Selected Approach

Add immutable economics contracts, a pure deterministic policy evaluator, lock-protected
in-memory policy and reservation adapters, and an administration service. Freeze the
active snapshot in run state at admission. The coordinator records a route-and-budget
decision before dispatch and invokes only the selected alias. Existing constructor calls
receive a frozen default policy store.

## Alternatives

* Routing inside model adapters was rejected because dependencies cannot own policy.
* Keyword-based complexity classification was rejected because task prose is not a
  governed signal; `high` and `critical` criticality select capable routing.
* Reactivating old snapshots during rollback was rejected because history must remain
  immutable; rollback creates a new version from an approved source.

## Validation

* A critical request dispatches `capable` first and records policy evidence.
* A 30-case corpus achieves at least 90 percent expected routing.
* Five over-budget cases start no disallowed paid operation.
* Every paid operation has a typed reservation receipt first.
* Update, denial, invalid proposal, stale version, and rollback paths preserve audit and
  active-version invariants.
* Ruff and all pytest suites pass under `.venv-x64`.
