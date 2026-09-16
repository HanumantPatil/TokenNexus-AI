<!-- markdownlint-disable-file -->

# Epic 1 Governed Orchestration Research

## Research Scope

Assess GitHub epic #1 and child issues #9, #10, and #11 to identify the smallest coherent Python 3.11+ implementation for governed, provider-neutral orchestration.

## Questions

* What module boundaries and dependencies are necessary?
* What strict contracts and closed vocabularies must be defined?
* What coordinator-owned state, idempotency, cancellation, deadline, retry, escalation, and budget invariants must hold?
* What deterministic provider-neutral substitutes are needed for tests?
* What focused test matrix proves the required behavior?

## Source Evidence

The assessment uses only the issue analysis and prior local research requested by the
user. No GitHub issue mutation or product-code change was made.

Primary evidence:

* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/issue-analysis.md
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/domain-contracts-reason-codes-research.md
* .copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md
* .copilot-tracking/research/subagents/2026-09-15/policy-evaluator-cache-defaults-research.md
* .copilot-tracking/research/subagents/2026-09-15/azure-ai-foundry-deployment-research.md
* .copilot-tracking/research/subagents/2026-09-15/foundry-model-selection-deep-research.md
* .copilot-tracking/research/subagents/2026-09-15/final-synthesis-coherence-review.md

The final synthesis coherence review resolves two stale shapes in an earlier domain
contract draft. The implementation must use one request-wide transient retry counter,
not one retry per operation. Quality values must remain on the evaluator-defined scale;
the `pilot-1` profile uses a 1-5 scale and threshold 4, not a silently normalized 0-1
value.

## Findings

### Epic Assessment

Epic #1 is coherent as one vertical control-plane slice if its three child issues remain
strictly separated by authority:

| Issue | Required ownership | Exit condition |
| --- | --- | --- |
| #9 | Public and internal versioned contracts, normalization, safe validation errors, canonical identity, and public reason validation | Valid documents normalize deterministically; invalid documents return field-specific RFC 9457 problems before a paid operation |
| #10 | Pure state reduction, journal claims, operation receipts, budget reservations, retry and escalation gates, cancellation, deadlines, and terminal projection | Replays and concurrency cannot duplicate paid work; no transition occurs after terminal state; quality attempts never exceed two |
| #11 | Provider-neutral model port, alias resolution boundary, result normalization, and scripted substitutes | Economical and capable implementations are interchangeable without changing contracts, policy, or coordinator behavior |

The epic should not add semantic cache, live evaluator logic, production pricing,
protected tools, telemetry export, Agent Framework orchestration, or Foundry clients.
Those later capabilities need ports now, but implementing them inside epic #1 would
mix policy domains and obscure the invariants this epic must prove.

### Smallest Coherent Python Package

Use Python 3.11+ and begin with a compact package whose files correspond to authority
boundaries rather than future infrastructure products.

```text
src/tokennexus/
	contracts.py          strict public, specialist, usage, result, and error types
	reasons.py            closed dotted public registry and status compatibility
	fingerprint.py        normalization projection, RFC 8785 bytes, SHA-256 fingerprint
	state.py              immutable RunState, events, transition table, pure reducer
	ports.py              Protocols for IDs, clock, journal, budget, model, and quality
	journal.py            atomic idempotency claim, CAS revision, receipts, reservations
	coordinator.py        the only transition and retry owner; executes approved effects
	problem_details.py    DomainError to RFC 9457 transport mapping
	adapters/
		deterministic.py    fake clock, UUID source, scripted models, evaluator, journal
		model_provider.py   production model adapter placeholder, outside domain authority
tests/
	contracts/
	orchestration/
	conformance/
```

Keep `model_provider.py` empty or absent until a provider is selected. Issue #11 can
complete against the port and scripted adapters. An Agent Framework workflow is also
unnecessary for this epic: the coordinator can later be wrapped by a framework, but
the framework must not become the reducer, retry owner, journal, or budget authority.

The import direction is one way:

```text
reasons <- contracts <- fingerprint
				<- state <- journal
contracts <- ports <- adapters
contracts + state + ports + journal + fingerprint <- coordinator
contracts + reasons <- problem_details
```

`coordinator.py` may depend on every core module. No lower module imports the
coordinator or an adapter. Provider SDK types never cross `ports.py`.

### Python Dependencies

Keep the runtime dependency set small and pin exact versions in the project lock file
after a compatibility spike.

| Dependency | Scope | Reason |
| --- | --- | --- |
| `pydantic` 2.x | Runtime | Strict frozen models, discriminated unions, closed objects, validators, and Draft 2020-12 schema export |
| `rfc8785` | Runtime | Standards-conformant JCS serialization; ordinary sorted JSON is not equivalent |
| `uuid6` | Runtime on Python 3.11-3.13 | RFC 9562 UUIDv7 generation until the minimum runtime provides `uuid.uuid7` |
| Python `hashlib`, `hmac`, `decimal`, `enum`, `typing`, `asyncio`, and `sqlite3` | Runtime standard library | Fingerprints, opaque-key hashing, exact arithmetic, closed vocabularies, ports, cancellation/deadlines, and a transactional local journal |
| `pytest` and `pytest-asyncio` | Development | Unit, concurrency, cancellation, and adapter conformance tests |
| `hypothesis` | Development | State-machine and cross-record invariant generation |
| `jsonschema` with format support | Development | Validate exported Draft 2020-12 schemas and golden wire fixtures independently of Pydantic |

FastAPI is optional. Add it only when issue #9 must expose HTTP in this increment;
`problem_details.py` should remain framework-neutral. Do not add a general retry
library such as Tenacity. The retry rule is small, request-wide, and must remain
visible in `RunState`. Do not use `orjson` or provider serialization to compute the
RFC 8785 fingerprint.

### Contract Rules

Every exchanged or persisted document has an exact `schema_version` and a stable
absolute schema identifier. Use independent Semantic Versions and JSON Schema Draft
2020-12. Public and specialist boundaries use `snake_case`, reject unknown properties,
reject duplicate JSON object names, and validate major-version compatibility before
domain processing.

Configure Pydantic boundary models as strict, frozen, and `extra="forbid"`. Do not use
model instances as mutable workflow state. Canonical money and quality values are
strings backed by `Decimal`; binary JSON floats, exponent notation, negative zero,
leading plus signs, and non-finite values are invalid.

The minimum contracts are:

* `PublicRequest`, `NormalizedRequest`, `PublicResult`, `DecisionSummary`,
	`DomainError`, and RFC 9457 `ProblemDetails`
* `PolicySnapshotRef`, `BudgetReservation`, `ModelInvocation`, `ModelOutcome`,
	`QualityEvaluation`, and `OperationReceipt`
* `SpecialistRequest` and `SpecialistResult` if the model adapter is represented as a
	bounded specialist
* `RunState`, coordinator event unions, `IdempotencyEntry`, and terminal result
	reference

The model result reports facts only: matching request, attempt, and operation IDs;
status; optional output; usage; receipts; registered reasons; and a bounded transient
classification. It cannot request a retry, choose another model, authorize an
escalation, or select a terminal state.

### UUIDv7 and Canonical Fingerprints

Inject an `IdSource` and generate UUIDv7 values for request, attempt, decision,
reservation, receipt, event, and error occurrence IDs. IDs are opaque correlation
values, never credentials. Tests use a deterministic sequence of valid UUIDv7 values;
production uses the compatibility library on Python 3.11-3.13.

Admission computes the request fingerprint only after structural and semantic
validation and default materialization. The closed fingerprint projection contains:

* Fingerprint profile and public contract major version
* Server-derived `scope_id` and public `application_id`
* Task content, content type, and order-sensitive mandatory context
* Effective constraints and cache directives
* An allowlisted authorization-context fingerprint only when claims change semantics

Exclude the idempotency key, generated IDs, timestamps, trace context, policy and
pricing versions, mutable counters, status, diagnostics, and response data. Preserve
task content after UTF-8 validation. Normalize product identifiers with Unicode NFC,
canonicalize decimal strings, serialize the closed projection with RFC 8785, then
store lowercase `sha256:<64 hex>`.

Hash the caller idempotency key separately with a server-held keyed HMAC. Never log or
persist the raw key.

### Validation Errors and Reason Codes

Domain validation produces a transport-neutral `DomainError` with JSON Pointer field
violations. The HTTP adapter maps it to RFC 9457 with stable `type`, `title`, HTTP
`status`, safe occurrence `detail`, and `instance`. Add a closed `invalid_params`
extension containing `path`, registered reason, and safe message for each invalid
field. Clients branch on problem `type`, terminal status, or a registered reason, not
on prose.

The public reason registry is a versioned immutable mapping. Initial epic coverage
must include at least:

```text
request.invalid
request.constraint_invalid
request.idempotency_conflict
request.cancelled_by_client
request.deadline_exceeded
budget.within_limit
budget.limit_exceeded
route.economical_eligible
route.capable_required
quality.threshold_met
quality.threshold_unmet
quality.evaluation_unavailable
escalation.quality_triggered
escalation.not_permitted_budget
escalation.not_permitted_latency
escalation.not_permitted_policy
dependency.model_unavailable
system.controlled_failure
```

Each registry entry declares allowed terminal statuses and retryability. Public reason
arrays are unique and lexically sorted. Unknown public codes, invalid code-to-status
combinations, underscore aliases, internal codes, provider exception strings, and
stack traces fail public serialization.

### Coordinator and State Machine

Implement `reduce(state, event) -> state` as a pure exhaustive function over closed
event unions. `RunState` is immutable and carries one normalized request, one frozen
policy reference, one absolute deadline, append-only evidence references, derived
totals, request-wide retry count, escalation count, and optional terminal outcome.
Only `coordinator.py` creates domain events and commits reducer outputs.

Use a small transition graph for this epic:

```text
admitted
	-> attempt_in_progress
	-> quality_pending
	-> completed
	-> escalation_pending -> attempt_in_progress -> quality_pending
	-> quality_unmet

admitted or any non-terminal state
	-> rejected | blocked | conflict | cancelled | timed_out | failed | degraded
```

Later epics may insert policy and cache states without changing terminal semantics.
The reducer rejects illegal predecessors, stale revisions, a second escalation, a
third quality attempt, mismatched identities, and every event after terminal state.
Terminal commit is first-writer-wins through journal compare-and-swap.

Separate pure decisions from effects. The coordinator first derives an approved
effect, persists its state and durable operation key, reserves its worst-case paid
allowance, checks cancellation and deadline again, and only then invokes a port. A
returned result is validated and journaled before the next reducer event is applied.

### Scoped Idempotency and Recovery

The durable key is `(scope_id, idempotency_key_hash)` with a unique storage constraint.
Admission uses one atomic create-or-read transaction:

| Existing entry | Fingerprint | Response | New external work |
| --- | --- | --- | --- |
| None | Not applicable | Create the request and in-progress entry | Allowed after commit |
| In progress | Equal | Return the same request ID and safe status | None |
| Terminal | Equal | Return the stored terminal result | None |
| Any | Different | RFC 9457 conflict with `request.idempotency_conflict` | None |

Use monotonic revision compare-and-swap for state updates. A worker lease coordinates
ownership but never authorizes a repeated effect. Every model dispatch has a durable
logical operation key. A centralized transport retry reuses that key and increments a
visible physical dispatch ordinal. Recovery checks receipts before dispatch. An
accepted, succeeded, failed, or unknown receipt prevents blind redispatch; an unknown
acknowledgement requires reconciliation.

For the first implementation, `sqlite3` is sufficient if transactions enforce the
unique claim, revision CAS, reservation, and receipt write rules. The test fake must
implement the same journal port and atomic semantics rather than a weaker dictionary
shortcut.

### Budget, Retry, Escalation, Cancellation, and Deadline

The hard counters have different meanings:

* `quality_attempt_count <= 2`
* `escalation_count <= 1`
* `transient_retries_consumed <= 1` across all remote dependencies for the request

A quality escalation creates attempt two, links `parent_attempt_id` to attempt one,
uses the capable alias, and receives a new operation key. A transient retry repeats the
same logical operation and attempt with the same operation key. Both consume the same
budget and non-resetting absolute deadline.

Before every physical paid dispatch, atomically reserve worst-case cost and token
allowance. Active plus committed reservations must fit the request ceiling. Reserve
again for the single physical retry because it may incur a second charge. Reconcile
actual usage after a valid receipt, but never let settlement authorize work that did
not fit before dispatch.

The coordinator may spend the one transient retry only for an allowlisted failure
that is known to precede an accepted response, is idempotent under the logical
operation key, and still fits budget and deadline. Authentication, authorization,
validation, policy, budget, malformed success, accepted or unknown acknowledgement,
and terminal errors are not retryable. Provider and SDK retries must be set to zero or
otherwise disabled. One call to `ModelPort.invoke` means exactly one provider transport
attempt.

Escalation requires all of these facts at once:

* Attempt one has a valid below-threshold quality evaluation
* No prior escalation exists
* Capable routing remains policy eligible
* Worst-case attempt-two model and evaluation cost is reserved
* Pessimistic attempt-two duration plus finalization reserve fits the absolute deadline
* The run is neither cancelled nor terminal

Evaluator unavailability produces quality unknown and the configured degraded result;
it is not evidence for escalation.

Store an absolute UTC deadline for evidence and use an injected monotonic clock to
calculate runtime remaining duration. Check cancellation and deadline before
reservation, after reservation and before dispatch, and after every await. Cancellation
or deadline expiry commits one terminal state and prevents new work. A late result may
create quarantined operational or accounting evidence, but cannot change run revision,
terminal result, counters, reservations, or authorize follow-on work.

### Provider-Neutral Model Boundary

Expose one narrow async port whose input and output are TokenNexus contracts. The port
accepts a stable alias (`economical` or `capable`), bounded input, absolute deadline,
logical operation key, visible transport ordinal, and approved generation limits. It
returns normalized output, usage, latency, receipt identity, and a bounded error
classification. It exposes no provider deployment name, endpoint, exception, response
object, SDK retry setting, or provider-specific tool type.

The production adapter resolves an alias from configuration and performs one SDK call.
The deterministic substitute is a scripted model keyed by fixture ID, alias, logical
operation key, and transport ordinal. Each script step returns one of:

* Successful normalized output with fixed usage and latency
* Known transient failure before acceptance
* Terminal provider failure
* Timeout or cancellation acknowledgement
* Malformed or identity-mismatched result for negative adapter tests

The substitute records an ordered immutable call log and raises on an unexpected call.
It never retries, routes, evaluates quality, mutates budget, or escalates. Running the
same script with the same fake clock and ID source must produce identical contracts,
reasons, transitions, receipts, and call counts.

### Required Invariants

The implementation is not complete unless executable tests prove all of these facts:

1. One request has exactly one normalized fingerprint, frozen policy reference, and
	 absolute deadline.
2. Every child record matches the admitted request and authenticated scope.
3. Attempt ordinals are contiguous and unique and never exceed two.
4. Attempt two has attempt one as parent and follows a recorded below-threshold result
	 plus an allowed escalation decision.
5. Escalation count never exceeds one and request-wide transient retries never exceed
	 one.
6. Active plus committed reservations never exceed cost, token, or tool ceilings.
7. Every physical paid dispatch has a prior active reservation and durable operation
	 key.
8. Same-scope exact replay returns the original run; different-fingerprint key reuse
	 conflicts; another scope remains isolated.
9. Cancellation or expired deadline prevents every new paid or side-effecting effect.
10. A terminal run never reopens, and late results cannot change its public outcome.
11. Specialists and model adapters cannot create state transitions or authoritative
		retries.
12. Public results contain only registered dotted reasons valid for their status.
13. Provider exceptions and internal diagnostics never cross the public boundary.
14. Disabling telemetry or replacing a provider does not change business decisions.
15. Hidden retries are absent: physical provider call count equals journaled dispatch
		count.

## Recommended Implementation Shape

Implement the epic in this order:

1. Freeze contract version `1.0.0`, primitive profiles, the initial dotted reason
	 registry, and golden normalization and fingerprint fixtures.
2. Implement immutable `RunState`, closed events, the legal transition table, and pure
	 reducer before any async orchestration.
3. Implement journal semantics and operation reservations with both a transactional
	 SQLite adapter and a behaviorally equivalent deterministic fake.
4. Implement the coordinator effect loop with injected clock, IDs, budget, quality,
	 journal, and model ports. Keep the request-wide retry policy here only.
5. Implement economical and capable scripted model substitutes and run the complete
	 epic suite without network or Azure dependencies.
6. Add the RFC 9457 HTTP adapter only if an HTTP endpoint is part of issue #9's agreed
	 increment.
7. Add a live provider adapter in a later integration increment after proving that its
	 SDK retries can be disabled and its cancellation, usage, timeout, and error behavior
	 passes the same conformance suite.

This sequence produces useful, testable value after each child issue while preserving
the dependency order: #9 contracts enable #10 state and journal records; #10 defines
the authority that consumes #11; #11 supplies deterministic execution without forcing
a production provider decision.

## Focused Test Matrix

| Area | Scenario | Required assertion | Issue |
| --- | --- | --- | --- |
| Contract | Valid request with omitted optional values | Defaults materialize before fingerprint; exported schema accepts the wire form | #9 |
| Contract | Unknown field, wrong type, duplicate property, bad decimal, or unsupported major | Rejected before journal claim or paid work | #9 |
| Error | Multiple invalid fields | RFC 9457 problem has stable type and JSON Pointer `invalid_params`; no internal detail leaks | #9 |
| IDs | Generated occurrence IDs | Every generated ID is valid UUIDv7; deterministic source preserves ordering | #9 |
| Fingerprint | Property reordering, trace changes, timestamp changes, or equivalent canonical decimal | Identical RFC 8785 bytes and SHA-256 fingerprint | #9 |
| Fingerprint | Scope, task content, mandatory-context order, or effective constraint changes | Different fingerprint | #9 |
| Reasons | Unknown code, underscore alias, duplicate code, or invalid status mapping | Public serialization fails closed; valid arrays are lexically sorted | #9 |
| Reducer | Every legal state transition | Exact expected next immutable state and revision | #10 |
| Reducer | Illegal predecessor, stale revision, event after terminal, second escalation, or third attempt | Transition rejected with no state mutation | #10 |
| Routine path | Passing economical result | One request, one attempt, one model call, one evaluation, one terminal result | #10/#11 |
| Escalation | Attempt one below threshold and all gates pass | Exactly two attempts; second links first; aliases are economical then capable | #10/#11 |
| Escalation denied | Budget, deadline, policy, cancellation, or prior escalation blocks attempt two | `quality_unmet` with the exact registered reason and no capable call | #10 |
| Evaluator unavailable | Valid model output but no score | Degraded quality-unknown result and no quality escalation | #10 |
| Retry | One allowlisted pre-acceptance transient failure | Same attempt and operation key, transport ordinal increments, one retry consumed, two reservations | #10/#11 |
| Retry exhausted | Two transient failures across one or two dependencies | No third physical dispatch anywhere in the request | #10 |
| Hidden retry | Invoke each production or scripted adapter once | Exactly one transport call; SDK retry configuration is disabled and observable | #11 |
| Reservation | Any paid model, evaluator, or retry dispatch | Active reservation exists first; concurrent totals never exceed ceiling | #10 |
| Budget race | Two workers try to reserve the final allowance | One CAS succeeds and at most one paid dispatch occurs | #10 |
| Replay in progress | Same scope, key, and fingerprint during active run | Same request and safe status; no additional model call | #10 |
| Replay terminal | Same scope, key, and fingerprint after completion | Byte-equivalent stored result; no model, evaluation, or mutation | #10 |
| Replay conflict | Same scope and key with changed fingerprint | HTTP 409 conflict and `request.idempotency_conflict`; no dispatch | #9/#10 |
| Scope isolation | Same opaque key in two authenticated scopes | Independent runs and no cross-scope result disclosure | #10 |
| Cancellation before dispatch | Cancellation arrives before or after reservation | No provider call; reservation is released when applicable; terminal is cancelled | #10 |
| Cancellation during await | Provider later returns success | Cancelled state and result remain unchanged; late evidence is quarantined | #10/#11 |
| Deadline | Fake clock crosses absolute deadline before retry or escalation | Timed-out terminal state; no new work; deadline never resets | #10 |
| Recovery | Crash after durable dispatch or unknown acknowledgement | Receipt check prevents blind redispatch; reconciliation is required | #10 |
| Adapter identity | Result echoes wrong request, attempt, operation key, or unsupported contract major | Result quarantined and never reduced into business state | #11 |
| Provider neutrality | Run identical scripts through economical and capable adapter registrations | Public and policy contracts are unchanged; only approved alias evidence differs | #11 |
| Determinism | Repeat frozen scenario with fake time and IDs | Identical result, reasons, transition log, receipts, and exact call counts | #10/#11 |
| Property state machine | Generated event sequences, budgets, deadlines, retries, and cancellations | All fifteen required invariants hold and terminal state is absorbing | #10 |

Run the focused unit and property suite before any live adapter conformance test. The
live suite may use tolerances for model content and latency, but it must retain exact
assertions for call count, retry ownership, identities, receipts, cancellation, and
public contract shape.

## Clarifying Questions

No clarification is required to start epic #1 if the following choices are treated as
explicit boundaries:

* Use the evaluator-defined 1-5 scale with threshold 4 for `pilot-1`; decide separately
	whether public `minimum_quality` remains in contract `1.0.0`.
* Return `blocked` for approval-required requests in this synchronous MVP; do not add a
	resumable public approval state inside this epic.
* Permit `quality_unmet` output only after product confirms whether bounded output or
	metadata-only behavior is desired. Tests can cover both behind a frozen policy flag.
* Select the durable production journal after the SQLite semantics and concurrency
	tests define the required port contract.
* Select the live provider only after confirming exact SDK retry-disable,
	idempotency, cancellation, timeout, usage, and acknowledgement behavior.
* Assign a stable HTTPS authority for schema IDs and RFC 9457 problem-type pages before
	publishing contract `1.0.0` externally.

These are schema publication and integration decisions. They do not block the pure
contracts, reducer, journal semantics, deterministic adapters, or focused test suite.
