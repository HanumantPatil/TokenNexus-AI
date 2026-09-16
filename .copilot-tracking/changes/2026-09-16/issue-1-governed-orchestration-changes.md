<!-- markdownlint-disable-file -->

# Issue 1 Governed Orchestration Changes

## Related Plan

`.copilot-tracking/plans/2026-09-16/issue-1-governed-orchestration-plan.instructions.md`

## Implementation Date

2026-09-16

## Summary

Implemented the first executable TokenNexus orchestration core for GitHub issue #1
and child issues #9, #10, and #11. The package provides strict contracts, canonical
request identity, deterministic orchestration, scoped idempotency, bounded paid work,
and provider-neutral scripted adapters.

## Added

* Python package and dependency configuration in `pyproject.toml` and `requirements.txt`
* Strict public and internal contracts under `src/tokennexus`
* Immutable state, journal, coordinator, model, budget, cancellation, and quality ports
* Deterministic scripted model and quality substitutes
* Contract and orchestration suites under `tests`
* Architecture guidance in `docs/architecture/governed-orchestration.md`

## Modified During Review

* Added safe nonterminal active replay with the original request identifier
* Added canonical UTC millisecond timestamps to public results
* Added the registered `request.in_progress` reason and unsupported-version tests
* Restricted source distributions to intended source, tests, docs, and metadata
* Aligned contract aliases, protocols, adapters, and test doubles with strict Pylance typing
* Typed the canonical fingerprint projection as recursive JSON data

## Removed

No existing project files were removed. The user-modified `README.md` was preserved.

## Validation

* Ruff passed for `src` and `tests`
* Pytest passed with 47 tests
* Fresh Pylance workspace diagnostics reported no errors
* Hatchling built the wheel and source distribution
* Wheel inspection found 14 members and no excluded paths
* Source distribution inspection found 23 members and no excluded paths

## Release Summary

TokenNexus now has a deterministic, provider-neutral orchestration kernel with strict
wire contracts, safe replay behavior, bounded retry and escalation, and executable
evidence for the issue #1 acceptance criteria.