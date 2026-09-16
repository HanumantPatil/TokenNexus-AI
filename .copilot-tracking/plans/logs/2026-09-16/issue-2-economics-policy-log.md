<!-- markdownlint-disable-file -->
---
title: Issue 2 Economics Policy Planning Log
description: Decisions, deviations, and follow-up notes for issue 2 implementation
ms.date: 2026-09-16
ms.topic: reference
---

## Selected Path

Use a pure policy evaluator and immutable admission snapshot. Keep execution authority in
the coordinator. Use typed multidimensional reservations and transactional in-memory
policy administration.

## Defaults

* `standard` routes economically when eligible; `high` and `critical` require capable.
* Approval-required is a non-executing blocked result in this release.
* Rollback clones an approved prior snapshot into a new version.
* Cost estimates use canonical decimal arithmetic and pessimistic token ceilings.

## Discrepancies

* The existing `BudgetPort` changed directly to the typed reservation contract instead
	of retaining a legacy money-only adapter. All local and test implementations were
	migrated in the same change.
* Invalid policy shapes are rejected by frozen Pydantic contracts before an
	administration command can be constructed. Authorized command conflicts and denied
	transitions remain safely audited by the administration service.
* The model protocol contains no route recommendation field. This structurally keeps
	route authority in the coordinator instead of adding an artificial ignored signal.

## Validation

* Ruff passed for `src`, `tests`, and `test.py`.
* The complete pytest suite passed with 100 tests.
* The 30-case routing corpus passed with exact repeated decisions.
* Five explicit over-budget coordinator cases and five ledger dimension denials passed.
* `git diff --check` reported no whitespace errors.

## Suggested Follow-On Work

* Replace in-memory stores with durable transactional adapters.
* Define a resumable approval workflow.
* Add an explicit versioned complexity signal rather than task-text heuristics.
