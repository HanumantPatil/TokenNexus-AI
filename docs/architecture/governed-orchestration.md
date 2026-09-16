---
title: Governed Request Orchestration
description: Architecture and developer guide for the TokenNexus deterministic orchestration core
ms.date: 2026-09-16
ms.topic: concept
---

## Scope

The TokenNexus core accepts strict, versioned requests and produces provider-neutral
terminal results. An application-owned coordinator controls admission, budget
reservation, model dispatch, quality evaluation, retry, escalation, cancellation,
deadlines, and terminalization.

The current package is an executable core, not an HTTP service. It includes an
in-memory journal and deterministic model and quality substitutes so policy behavior
can be tested without Azure or provider SDKs.

## Install dependencies

Create the repository-local environment, then install the project and development
dependencies through the approved package feed:

```powershell
uv venv .venv-x64
uv pip install --python .venv-x64\Scripts\python.exe --index-url https://packagefeedproxy.microsoft.io/pypi/simple/ -r requirements.txt .
```

Run checks through the environment interpreter to avoid an implicit `uv run` sync
against another package index:

```powershell
.venv-x64\Scripts\python.exe -m pytest -q
.venv-x64\Scripts\ruff.exe check src tests
```

## Core flow

1. `PublicRequest` validates the versioned boundary and rejects unknown fields.
2. `normalize_request` materializes defaults, scope, and a UUIDv7 request identifier.
3. `request_fingerprint` applies RFC 8785 canonical JSON and SHA-256.
4. `Journal.claim` atomically admits a scoped idempotency key, returns an exact replay,
   or reports a fingerprint conflict.
5. `Coordinator` checks cancellation and the absolute deadline before controlled work.
6. The coordinator reserves budget before every model or quality operation.
7. The economical alias runs first. Low quality can trigger one capable-model
   escalation.
8. The first terminal result wins and becomes immutable for every later replay.

## Invariants

* Exact replays return the stored terminal object without another paid operation.
* A changed fingerprint under the same scope and key conflicts before execution.
* Every model dispatch and quality evaluation follows a successful budget reservation.
* One request permits at most two model attempts and two quality evaluations.
* One request permits at most one capable-model escalation.
* One centralized transient model retry is available across the entire request.
* Late results cannot mutate cancelled, timed-out, or otherwise terminal runs.
* Model and quality ports report facts. They do not select routes or retry internally.
* Public reason codes come from the closed registry in `tokennexus.reasons`.

## Deterministic substitutes

`ScriptedModelPort` and `ScriptedQualityEvaluator` consume immutable scripts. Each
invocation records one immutable call and consumes one configured step. Exhausted
scripts fail explicitly, which exposes unexpected work in policy tests.

Both economical and capable aliases use the same `ModelInvocation` and `ModelOutcome`
contracts. A successful outcome includes output, token usage, estimated cost, and
provider latency. Failed outcomes omit output and usage and expose only registered safe
reason codes.

## Production boundaries

The following integrations remain behind ports and are not part of this core slice:

* Durable journal storage and crash recovery
* Live provider SDK adapters and deployment aliases
* Authentication, HTTP hosting, and RFC 9457 transport mapping
* Semantic cache storage
* Production budget ledger and cancellation source

A live model adapter must disable provider SDK retries or expose each retry to the
coordinator. A durable journal must preserve atomic claim, compare-and-set, and
first-terminal-wins semantics across processes.
