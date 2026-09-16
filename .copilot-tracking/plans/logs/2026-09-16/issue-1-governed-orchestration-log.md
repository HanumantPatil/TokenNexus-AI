<!-- markdownlint-disable-file -->

# Issue 1 Governed Orchestration Planning Log

## Selected Path

Implement a dependency-light Python core with explicit ports and deterministic
substitutes. This is the smallest path that proves the epic without choosing unresolved
Azure models, infrastructure, or a reference application domain.

## Alternatives Considered

* Microsoft Agent Framework workflow: deferred because the coordinator invariants can
  be proved directly and the framework must not own policy or state transitions.
* FastAPI endpoint: deferred because RFC 9457 transport contracts can be tested without
  introducing a server before the API hosting story is defined.
* Live Foundry adapters: deferred because model deployments, region, credentials, and
  SDK retry behavior remain open product and infrastructure decisions.
* SQLite journal: deferred behind the journal contract; this epic proves transaction
  semantics with a lock-protected implementation before selecting production storage.

## Discrepancies

* The earlier domain research described both per-operation and request-wide transient
  retry limits. The final synthesis and issue #10 require one centralized request-wide
  retry allowance, which this plan adopts.
* The user-modified README contains issue-generation status text. It will not be
  reformatted or removed as part of this implementation.
* Initial review found that exact active replay raised an exception and public results
  omitted canonical timestamps. The implementation now returns a nonterminal
  `in_progress` result and emits strict UTC millisecond timestamps.
* The first source distribution captured `.venv-x64` and `.copilot-tracking` because
  only the wheel target selected files. An explicit sdist allowlist corrected the
  package boundary before final review.

## Validation Record

* `.venv-x64\Scripts\ruff.exe check src tests`: passed
* `.venv-x64\Scripts\python.exe -m pytest -q`: 47 passed
* `.venv-x64\Scripts\python.exe -m hatchling build`: passed
* Final wheel size: 20,811 bytes
* Final source distribution size: 25,837 bytes with 23 members
* Package inspection found no virtual environment, tracking, distribution, Git, or
  cache paths.

## Suggested Follow-On Work

* Add a durable SQLite journal adapter with concurrency and crash-recovery tests.
* Publish generated JSON Schemas under a stable HTTPS schema authority.
* Add a live provider adapter after selecting deployments and proving SDK retries are disabled.