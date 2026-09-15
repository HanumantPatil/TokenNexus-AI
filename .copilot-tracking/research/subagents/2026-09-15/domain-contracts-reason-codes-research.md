---
title: Domain Contracts and Public Reason Codes Research
description: Planning-ready language-neutral contracts for TokenNexus-AI-Framework execution and evidence
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: concept
---

## Research Scope

Specify planning-ready, language-neutral schemas for the TokenNexus-AI-Framework public API, specialist boundary, coordinator state, policy evidence, execution records, idempotency, capabilities, errors, statuses, and reason codes.

The research evaluates schema versioning, money, timestamps, identifiers, invariants, compatibility, validation boundaries, canonical request hashing, replay behavior, and PRD traceability. It selects one coherent approach and records unresolved product inputs without reopening the application-owned control-plane decision.

## Research Questions

* Which JSON Schema dialect and versioning policy should govern public and internal contracts?
* How should public requests, results, specialist messages, run state, policy snapshots, execution records, journal entries, grants, receipts, errors, statuses, and reason codes be represented?
* Which invariants belong in JSON Schema, deterministic domain validation, storage constraints, and adapter boundaries?
* How should canonical request hashes distinguish exact replay from idempotency conflict?
* How should every contract field map to the PRD?

## Findings

### Executive Recommendation

Adopt one language-neutral contract family with these fixed choices:

* JSON Schema Draft 2020-12 for every persisted or exchanged JSON document
* Absolute, stable schema identifiers and Semantic Versioning for contract versions
* UTF-8 JSON with strings for decimal money and RFC 3339 UTC timestamps
* UUIDv7 for generated request, attempt, decision, grant, receipt, and event IDs
* RFC 8785 JSON Canonicalization Scheme (JCS) plus SHA-256 for request fingerprints
* Immutable admission data and append-only decision, reservation, attempt, receipt,
  evaluation, and event records
* A closed public reason-code registry separate from an extensible internal diagnostic
  registry
* An application-owned coordinator as the only authority for routing, budget,
  escalation, authorization, and terminal-state transitions
* A durable idempotency journal as the authority for replay and duplicate side-effect
  suppression, independent of workflow checkpoints

The family should use `snake_case` JSON property names and lowercase underscore enum
values. Unknown object properties are rejected at trust boundaries. Open metadata bags
are not part of the MVP contracts because they weaken compatibility analysis, privacy
review, and canonical hashing.

### Standards Basis

| Topic | Selected standard | Consequence |
| --- | --- | --- |
| JSON schema | JSON Schema Draft 2020-12 Core and Validation | Every schema declares `$schema` and an absolute `$id`; critical semantic checks do not rely on `format` alone |
| Versioning | Semantic Versioning 2.0.0 | Major versions may break consumers; minor versions are additive; patch versions clarify constraints without changing accepted instances |
| Canonical JSON | RFC 8785 JCS | Fingerprint projections use deterministic UTF-8 serialization and lexicographically sorted object properties |
| Hash | SHA-256 | Fingerprints are written as lowercase `sha256:<64 hex characters>` strings |
| Time | RFC 3339 profile | Generated timestamps use uppercase `T` and `Z`, UTC only, with exactly three fractional digits |
| IDs | RFC 9562 UUIDv7 | IDs are time-sortable occurrences, but never credentials or authorization capabilities |
| HTTP errors | RFC 9457 Problem Details | HTTP adapters translate domain errors to safe problem documents; domain contracts remain transport-neutral |

Authoritative references:

* [JSON Schema Draft 2020-12 Core](https://json-schema.org/draft/2020-12/json-schema-core)
* [JSON Schema Draft 2020-12 Validation](https://json-schema.org/draft/2020-12/json-schema-validation)
* [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)
* [RFC 3339 Date and Time on the Internet](https://www.rfc-editor.org/rfc/rfc3339)
* [RFC 9562 Universally Unique IDentifiers](https://www.rfc-editor.org/rfc/rfc9562)
* [RFC 9457 Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
* [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html)

### Common Contract Primitives

The implementation should publish shared definitions and reference them from every
schema. The following profiles remove cross-language ambiguity.

| Primitive | Wire representation | Rules |
| --- | --- | --- |
| `schema_version` | String | Exact `MAJOR.MINOR.PATCH`; identifies the document contract, not policy or provider versions |
| Domain ID | String | Canonical lowercase hyphenated UUID; generated IDs use UUIDv7; callers treat all IDs as opaque |
| Timestamp | String | `YYYY-MM-DDTHH:mm:ss.sssZ`; leap seconds are not generated; compare as instants after parsing |
| Duration | Integer | Non-negative milliseconds with a field-specific maximum |
| Count | Integer | Non-negative base-10 JSON integer within the field-specific maximum |
| Ratio or score | String | Canonical decimal string between declared inclusive bounds |
| Money | Object | ISO 4217 uppercase `currency` plus canonical decimal-string `amount` |
| Fingerprint | String | `sha256:` followed by 64 lowercase hexadecimal characters |
| Reason code | String | Lowercase dotted identifier from a versioned registry |
| Model alias | String | Stable product alias, not a provider deployment name or credential-bearing endpoint |
| Component name | String | Closed product component enum for public data; internal diagnostics may add registered components |

Canonical decimal strings use this grammar:

```text
0|[1-9][0-9]*(\.[0-9]*[1-9])?
```

Negative zero, a leading plus sign, leading zeros, exponent notation, `NaN`, and
infinity are forbidden. Domain-specific schemas add scale and range constraints. For
MVP money, support non-negative values with at most six fractional digits. Arithmetic
uses decimal or integer-minor-unit types, never binary floating point. The canonical
zero is `"0"`.

Use these shared money and trace shapes:

```json
{
  "money": {
    "currency": "USD",
    "amount": "0.001275"
  },
  "trace_context": {
    "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    "tracestate": "vendor=value"
  }
}
```

Trace context is operational correlation only. It is excluded from request identity,
authorization, policy decisions, and idempotency fingerprints.

### Schema Family and Ownership

| Schema | Producer | Authoritative consumer | Durability | Compatibility surface |
| --- | --- | --- | --- | --- |
| `public-request` | API adapter | Coordinator admission | Journaled projection | Public |
| `public-result` | Coordinator | API adapter and client | Terminal response | Public |
| `policy-snapshot` | Policy store | Coordinator | Immutable evidence | Internal governance |
| `routing-decision` | Coordinator | Run state and execution record | Append-only | Internal evidence |
| `specialist-request` | Coordinator | Specialist adapter | Dispatch journal | Internal boundary |
| `specialist-result` | Specialist adapter | Coordinator | Attempt evidence | Internal boundary |
| `budget-reservation` | Coordinator | Budget ledger | Append-only | Internal evidence |
| `quality-evaluation` | Evaluator adapter | Coordinator | Append-only | Internal evidence |
| `capability-grant` | Authorization service | Capability facade | Immutable and expiring | Security boundary |
| `operation-receipt` | Provider or tool facade | Journal and coordinator | Append-only | Side-effect evidence |
| `run-state` | Coordinator reducer | Coordinator | Snapshot plus event references | Internal recovery |
| `execution-record` | Coordinator projector | Analytics and audit | Immutable terminal record | Evidence |
| `idempotency-entry` | Journal | Admission and recovery | Durable mutable status with append-only history | Reliability boundary |
| `domain-error` | Any trusted component | Coordinator | Evidence and safe translation | Internal |
| `public-decision-summary` | Coordinator | Client | Embedded in result | Public |

Each document includes `schema_version`. Persisted records also include a unique record
ID and `recorded_at_utc`. Embedding one document inside another does not transfer
authority. For example, a specialist may echo grant and budget data, but only the
coordinator dispatch record and server-side ledger are authoritative.

### Public Request Contract

The public request contains caller intent and declared constraints. Authenticated
identity, roles, tenant, application scope, server time, policy version, and request ID
are server-derived admission facts and must not be accepted from the request body.

```json
{
  "schema_version": "1.0.0",
  "idempotency_key": "client-generated-opaque-value",
  "application_id": "claims-assistant",
  "task": {
    "content": "Summarize the approved claim evidence.",
    "content_type": "text/plain",
    "mandatory_context": [
      {
        "context_id": "policy-instruction-1",
        "kind": "instruction",
        "content": "Cite the supplied evidence only."
      }
    ]
  },
  "constraints": {
    "criticality": "standard",
    "minimum_quality": "0.85",
    "maximum_latency_ms": 10000,
    "maximum_budget": {
      "currency": "USD",
      "amount": "0.02"
    },
    "maximum_input_tokens": 8000,
    "maximum_output_tokens": 1000,
    "maximum_tool_calls": 1
  },
  "cache_directives": {
    "eligible": true,
    "freshness": "standard",
    "maximum_entry_age_ms": 3600000,
    "sensitivity": "non_sensitive"
  }
}
```

Required fields are `schema_version`, `idempotency_key`, `application_id`, `task`,
`constraints`, and `cache_directives`. The API permits omission of individual optional
constraint values, but admission normalization materializes every effective value from
documented policy defaults before hashing. Empty task content, unknown content types,
unsupported currencies, contradictory cache directives, and values outside policy
ceilings are rejected before a request ID or paid operation is created.

The body must not contain credentials, provider endpoints, policy overrides, model
deployment names, role claims, capability grants, routing instructions, or raw tool
definitions. The adapter treats these as unknown properties and rejects them.

### Admission and Normalized Request

Admission creates an immutable internal request containing:

| Field | Source | Purpose |
| --- | --- | --- |
| `request_id` | Server UUIDv7 generator | Stable business correlation across all paths |
| `scope_id` | Authenticated tenant and application claims | Idempotency, cache, and authorization isolation |
| `actor_id_hash` | Server-side keyed pseudonymization | Audit linkage without persisting direct identity |
| `actor_roles` | Validated authorization context | Protected-action checks |
| `received_at_utc` | Injected server clock | Admission evidence and deadline derivation |
| `absolute_deadline_utc` | Server calculation | Non-resetting parent deadline |
| `normalized_request` | Deterministic normalizer | Complete effective request used by policy and hashing |
| `request_fingerprint` | Canonical hash procedure | Exact replay comparison |
| `policy_snapshot_id` | Policy resolver | Frozen behavior configuration |

Normalization performs Unicode NFC normalization on textual identifiers but does not
rewrite user task content. It validates content encoding, materializes defaults, sorts
sets such as role or capability names, preserves order-sensitive arrays such as
mandatory context, and converts decimal values to their canonical string form.

### Policy Snapshot Contract

The snapshot is immutable evidence resolved once at admission. Mid-run policy changes
never alter the current request.

```json
{
  "schema_version": "1.0.0",
  "policy_snapshot_id": "018f0e7c-7b5a-7cc4-98c4-1f9a85e36b01",
  "policy_version": "2026-09-15.1",
  "pricing_version": "2026-09-15.1",
  "evaluator_version": "rubric-1.0.0",
  "cache_policy_version": "cache-1.0.0",
  "authorization_policy_version": "authz-1.0.0",
  "effective_at_utc": "2026-09-15T12:00:00.000Z",
  "model_tiers": ["economical", "capable"],
  "limits": {
    "maximum_escalations": 1,
    "maximum_tool_calls": 1,
    "maximum_transient_retries_per_operation": 1
  },
  "snapshot_fingerprint": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

The full snapshot includes routing rules, fixed prices, quality thresholds, cache
rules, timeout profiles, capability rules, and public-reason mappings. Secrets,
deployment credentials, and raw authorization tokens are references resolved by
adapters and are never stored in the snapshot. `snapshot_fingerprint` is computed over
the snapshot projection without that field or storage metadata.

### Routing and Budget Contracts

A routing decision records facts evaluated by the coordinator. It does not contain
free-form model reasoning.

```text
RoutingDecision
  schema_version
  decision_id
  request_id
  decision_kind              # admission, budget, cache, route, escalation, terminal
  sequence_number
  policy_snapshot_id
  outcome                    # allowed, denied, required, skipped, selected
  selected_model_alias?
  public_reason_codes[]
  internal_reason_codes[]
  evaluated_facts[]          # typed name, operator, redacted value, result
  decided_at_utc
```

Reason arrays are sets serialized in ascending lexical order. A decision has at least
one reason code. `evaluated_facts` uses an allowlisted vocabulary and may contain
classified or bucketed values, not task content, hidden prompts, credentials, or
provider exception text.

Every paid operation has a preceding budget reservation:

```text
BudgetReservation
  schema_version
  reservation_id
  request_id
  attempt_id?
  operation_key
  sequence_number
  pricing_version
  reserved_cost
  reserved_input_tokens
  reserved_output_tokens
  reserved_tool_calls
  status                     # reserved, committed, released
  created_at_utc
  settled_at_utc?
  actual_usage_reference?
```

The ledger guarantees that committed plus active reservations never exceed request
ceilings. Settlement may reduce a reservation or record bounded overage evidence, but
it cannot authorize another operation after the original ceiling is exhausted.

### Specialist Request Contract

The request is a bounded command, not a transfer of routing authority.

```text
SpecialistRequest
  schema_version
  request_id
  attempt_id
  parent_attempt_id?
  attempt_ordinal            # 1 or 2
  operation_key
  specialist_kind
  task
  mandatory_context[]
  declared_constraints
  policy_snapshot_id
  policy_version
  route_reason_codes[]
  absolute_deadline_utc
  remaining_budget
    maximum_cost
    maximum_input_tokens
    maximum_output_tokens
    maximum_tool_calls
  escalation_count           # 0 or 1
  capability_grant_ids[]
  trace_context
```

The specialist receives only the task data required for the selected operation.
Authenticated identity and unrestricted policy are omitted. `operation_key` is stable
across a transport retry of the same logical invocation. A quality escalation receives
a new `attempt_id` and operation key. Transport retries do not increment
`attempt_ordinal` or `escalation_count`.

The coordinator rejects dispatch unless all of these conditions hold:

* The request and policy snapshot are immutable and valid
* The run is non-terminal and non-cancelled
* The deadline has not expired
* A matching active reservation exists
* Attempt ordinal is one or two
* Attempt two has attempt one as its parent and escalation count equals one
* Every grant belongs to the same request and attempt and expires no later than the
  request deadline

### Specialist Result Contract

The result reports observed facts and a bounded classification. It never commands a
retry, model change, escalation, alternate tool call, or terminal state.

```text
SpecialistResult
  schema_version
  request_id
  attempt_id
  operation_key
  status                     # succeeded, failed, cancelled, timed_out
  output?
    content
    content_type
  usage
    input_tokens
    output_tokens
    estimated_cost
    provider_latency_ms
    tool_call_count
  operation_receipt_ids[]
  specialist_reason_codes[]
  retry_classification       # none, transient, terminal
  error?
    domain_error_id
    code
    safe_message
    component
  completed_at_utc
```

The adapter validates the result before the coordinator can reduce it into state. It
must match dispatch `request_id`, `attempt_id`, `operation_key`, contract major version,
and all receipt identities. Usage values are reconciled against provider or facade
receipts. A success requires output and forbids `error`; a non-success forbids output
unless an explicitly supported partial-output contract is introduced in a later major
version.

### Quality Evaluation Contract

```text
QualityEvaluation
  schema_version
  evaluation_id
  request_id
  attempt_id
  evaluator_method
  evaluator_version
  score?                     # canonical decimal string from 0 through 1
  threshold                  # canonical decimal string from 0 through 1
  outcome                    # passed, below_threshold, unavailable, invalid
  public_reason_codes[]
  internal_reason_codes[]
  evaluated_at_utc
  latency_ms
```

`passed` requires `score >= threshold`; `below_threshold` requires `score < threshold`.
`unavailable` and `invalid` omit the score. Evaluator failure does not imply poor
quality and cannot independently authorize escalation. The coordinator follows the
frozen degraded-state policy.

### Capability Grant and Operation Receipt Contracts

A capability grant is server-signed or stored behind an opaque ID. The ID alone is not
the capability.

```text
CapabilityGrant
  schema_version
  grant_id
  request_id
  attempt_id
  subject_component
  tool_name
  allowed_operation
  argument_schema_id
  argument_constraints_fingerprint
  maximum_calls
  authorization_decision_id
  issued_at_utc
  expires_at_utc
  grant_status               # active, consumed, revoked, expired
```

The capability facade resolves the grant, rechecks authorization, validates arguments,
enforces call count and deadline, derives a stable child operation key, and writes a
receipt before returning to the specialist.

```text
OperationReceipt
  schema_version
  receipt_id
  request_id
  attempt_id
  grant_id?
  operation_key
  operation_kind             # model, tool, cache_read, approval, telemetry
  component
  status                     # accepted, succeeded, failed, unknown
  provider_operation_id_hash?
  request_payload_fingerprint
  response_payload_fingerprint?
  actual_usage?
  started_at_utc
  completed_at_utc?
  internal_reason_codes[]
```

Receipt fingerprints use redacted semantic projections. They prove equality for
duplicate suppression, not payload authenticity. Raw provider IDs are hashed when they
could reveal account or deployment information.

### Run State Contract

`RunState` is an explicit reducer output. It contains immutable admission data,
append-only references, and derived totals. It is not directly edited by specialists,
telemetry processors, or UI clients.

```text
RunState
  schema_version
  request_id
  revision                   # monotonic compare-and-swap integer
  admitted_request
  policy_snapshot_id
  request_fingerprint
  absolute_deadline_utc
  lifecycle_status
  cancellation?
    requested_at_utc
    source
  decision_ids[]
  reservation_ids[]
  attempt_ids[]
  evaluation_ids[]
  grant_ids[]
  receipt_ids[]
  derived_totals
    committed_cost
    input_tokens
    output_tokens
    tool_calls
    escalation_count
  terminal?
    status
    public_reason_codes[]
    terminal_decision_id
    completed_at_utc
```

Allowed lifecycle states are:

```text
admitted
policy_evaluated
cache_evaluated
attempt_in_progress
quality_pending
escalation_pending
approval_pending
completed
degraded
quality_unmet
rejected
blocked
conflict
cancelled
timed_out
failed
```

The terminal states are `completed`, `degraded`, `quality_unmet`, `rejected`,
`blocked`, `conflict`, `cancelled`, `timed_out`, and `failed`. A successful idempotent
replay returns the stored state but does not add another business transition. Late
results may add quarantined operational evidence, but cannot increment run revision,
settle new business usage, alter the result, or reopen a terminal run.

### Idempotency Entry Contract

The idempotency key namespace is `(scope_id, idempotency_key)`. The journal performs an
atomic create-or-read before assigning paid work.

```text
IdempotencyEntry
  schema_version
  scope_id
  idempotency_key_hash
  request_id
  request_fingerprint
  status                     # in_progress, terminal
  run_revision
  terminal_result_reference?
  lease_owner?
  lease_expires_at_utc?
  created_at_utc
  updated_at_utc
  operation_receipt_ids[]
```

Store a keyed hash of the caller idempotency key rather than the raw key. The key is
opaque, has a documented maximum length, and is never logged. A lease coordinates
workers but does not authorize repeated external operations. Recovery always examines
operation receipts before dispatch.

### Execution Record Contract

The execution record is an immutable terminal projection for economics, governance,
and evaluation. It references detailed evidence rather than embedding secrets or raw
content.

```text
ExecutionRecord
  schema_version
  execution_record_id
  request_id
  request_fingerprint
  application_id
  scope_id
  received_at_utc
  completed_at_utc
  declared_constraints
  policy_snapshot_id
  policy_version
  pricing_version
  selected_model_aliases[]
  public_reason_codes[]
  input_tokens
  output_tokens
  cached_tokens
  avoided_tokens
  estimated_actual_cost
  estimated_all_frontier_cost
  end_to_end_latency_ms
  orchestration_latency_ms
  provider_latency_ms
  quality
    status
    score?
    threshold
    evaluator_method
    evaluator_version
  cache
    status
    public_bypass_reason?
    scope
    entry_age_ms?
  escalation
    status
    public_reason?
    attempt_ids[]
  tools
    call_count
    bounded_path_status
  component_statuses[]
  feedback_reference?
  evidence_references[]
```

The projection must reconcile with journal facts. An execution record cannot be
created for a non-terminal run. Raw prompts, raw responses, capability material,
authorization tokens, internal diagnostics, stack traces, and provider deployment
names are excluded by default.

### Public Result and Decision Summary

```json
{
  "schema_version": "1.0.0",
  "request_id": "018f0e7c-7b5a-7cc4-98c4-1f9a85e36b01",
  "status": "completed",
  "output": {
    "content": "The approved evidence indicates...",
    "content_type": "text/plain"
  },
  "decision_summary": {
    "model_alias": "economical",
    "estimated_cost": {
      "currency": "USD",
      "amount": "0.001275"
    },
    "latency_ms": 1840,
    "quality": {
      "status": "passed",
      "score": "0.91",
      "threshold": "0.85"
    },
    "cache_status": "miss",
    "escalation_status": "not_required",
    "public_reason_codes": ["route.economical_eligible"]
  }
}
```

The public status vocabulary matches terminal `RunState` values. Results with
`completed` require output. `degraded` may contain output when the configured degraded
path produced a usable answer. `quality_unmet` may contain a policy-approved bounded
output plus an explicit warning. `rejected`, `blocked`, `conflict`, `cancelled`,
`timed_out`, and `failed` omit output and include a safe error.

### Domain Error and HTTP Representation

The transport-neutral error is:

```text
DomainError
  schema_version
  domain_error_id
  request_id?
  code                       # stable internal error code
  public_reason_code
  safe_message
  component
  retry_classification       # none, transient, terminal
  field_violations[]?
    path                     # JSON Pointer into caller document
    public_reason_code
    safe_message
  occurred_at_utc
  internal_diagnostic_id?
```

HTTP adapters map it to RFC 9457. `type` is a stable HTTPS URI documenting the public
reason, `title` is stable for the problem type, `status` is the HTTP status, `detail`
is occurrence-specific but safe, and `instance` identifies the occurrence without
exposing infrastructure. Clients branch on `type` or `public_reason_code`, never on
`title`, `detail`, or localized text.

```json
{
  "type": "https://tokennexus.example/problems/idempotency-conflict",
  "title": "Idempotency key conflict",
  "status": 409,
  "detail": "The idempotency key was already used for a different request.",
  "instance": "/requests/018f0e7c-7b5a-7cc4-98c4-1f9a85e36b01/errors/018f0e7d-1c29-7a1e-a5f8-39c678f81f31",
  "request_id": "018f0e7c-7b5a-7cc4-98c4-1f9a85e36b01",
  "public_reason_code": "request.idempotency_conflict"
}
```

### Public Reason-Code Registry

Public reasons explain product decisions without exposing hidden prompts, policy rule
expressions, credentials, deployment details, security detection logic, provider
exceptions, or user data. The registry is closed and centrally owned by product and
governance. Every entry contains `code`, `introduced_in`, `status`, `category`,
`default_severity`, `retryable`, `allowed_public_statuses`, `safe_title`,
`safe_message_template`, `owner`, and `replacement_code` when deprecated.

| Code | Meaning | Statuses | Retryable |
| --- | --- | --- | --- |
| `request.invalid` | The request envelope is invalid | `rejected` | No |
| `request.constraint_invalid` | A declared constraint is malformed or unsupported | `rejected` | No |
| `request.idempotency_conflict` | The same scoped key names a different request fingerprint | `conflict` | No |
| `request.cancelled_by_client` | The authenticated client cancelled the run | `cancelled` | No |
| `request.deadline_exceeded` | The absolute request deadline expired | `timed_out` | Conditional new request |
| `policy.request_allowed` | Frozen policy permits routine processing | `completed`, `degraded`, `quality_unmet` | No |
| `policy.request_blocked` | Frozen policy denies processing | `blocked` | No |
| `route.economical_eligible` | The economical tier satisfies eligibility gates | `completed`, `degraded`, `quality_unmet` | No |
| `route.capable_required` | Quality, criticality, or task rules require the capable tier | `completed`, `degraded`, `quality_unmet` | No |
| `budget.within_limit` | Estimated cost fits the request ceiling | `completed`, `degraded`, `quality_unmet` | No |
| `budget.downgrade_required` | Budget permits only a lower-cost eligible path | `completed`, `degraded`, `quality_unmet` | No |
| `budget.limit_exceeded` | No paid path fits the cost ceiling | `blocked`, `quality_unmet` | No |
| `budget.approval_required` | Cost requires an authorized approval | `blocked` or pending response extension | After approval |
| `latency.escalation_forbidden` | Remaining time cannot accommodate escalation | `quality_unmet` | No |
| `cache.hit_eligible` | An eligible scoped cache result was reused | `completed` | No |
| `cache.miss` | No eligible cache result was found | `completed`, `degraded`, `quality_unmet` | No |
| `cache.bypassed_sensitive` | Sensitivity rules prohibited cache use | `completed`, `degraded`, `quality_unmet` | No |
| `cache.bypassed_freshness` | Freshness rules prohibited cache use | `completed`, `degraded`, `quality_unmet` | No |
| `cache.bypassed_policy` | Frozen policy prohibited cache use | `completed`, `degraded`, `quality_unmet` | No |
| `quality.threshold_met` | Evaluation met the configured threshold | `completed` | No |
| `quality.threshold_unmet` | Evaluation was below the configured threshold | `quality_unmet` | No |
| `quality.evaluation_unavailable` | Quality could not be evaluated | `degraded` | No |
| `escalation.quality_triggered` | A below-threshold result triggered the single escalation | `completed`, `quality_unmet` | No |
| `escalation.not_permitted_budget` | Remaining budget prohibited escalation | `quality_unmet` | No |
| `escalation.not_permitted_latency` | Remaining time prohibited escalation | `quality_unmet` | No |
| `escalation.not_permitted_policy` | Frozen policy prohibited escalation | `quality_unmet` | No |
| `authorization.denied` | The actor is not permitted to perform the action | `blocked` | No |
| `tool.not_granted` | The requested product tool was not granted | `blocked` | No |
| `tool.argument_rejected` | Tool arguments exceeded the configured contract | `blocked` | No |
| `tool.call_limit_exceeded` | The request reached its tool-call ceiling | `blocked`, `quality_unmet` | No |
| `dependency.model_unavailable` | An eligible model path was unavailable | `failed`, `degraded` | Conditional new request |
| `dependency.telemetry_degraded` | Non-authoritative telemetry enrichment failed | `degraded` | No |
| `system.controlled_failure` | Processing failed without a more specific safe reason | `failed` | Conditional |

`budget.approval_required` needs a product decision about whether the synchronous
public API gains a non-terminal `approval_pending` response. Until that decision is
made, the MVP should return `blocked` with a new-request recovery action after approval.

### Internal Diagnostic Registry

Internal codes identify operational mechanisms and may be more specific, but still
must not contain secrets or personal data. Use the form
`internal.<component>.<condition>`, for example:

```text
internal.provider.timeout
internal.provider.rate_limited
internal.provider.acknowledgement_unknown
internal.evaluator.invalid_score
internal.cache.scope_mismatch
internal.cache.entry_expired
internal.authorization.grant_expired
internal.authorization.signature_invalid
internal.tool.argument_schema_failed
internal.journal.write_conflict
internal.journal.receipt_missing
internal.telemetry.export_failed
internal.contract.unsupported_major
internal.contract.identity_mismatch
```

Every internal code maps to exactly one public reason or to no public reason when it is
non-material telemetry. The mapping is versioned in policy. Provider error strings,
HTTP bodies, stack traces, rule expressions, and exception class names remain in
restricted diagnostics and never become reason codes.

### Registry Governance and Compatibility

The registry follows these rules:

1. A code's semantic meaning never changes.
2. New codes may be added in a registry minor version.
3. Consumers must tolerate unknown reason codes while continuing to use status and
   known codes.
4. A code may be deprecated but remains accepted and documented through the current
   contract major version.
5. A replacement is a new code with an explicit `replacement_code`; historical
   records are not rewritten.
6. Removing or reusing a code requires a new contract major version.
7. Public code templates are security reviewed and localization-safe.
8. Each decision stores the registry version used to validate its reasons.
9. Tests verify allowed code-to-status combinations and ensure internal-only codes
   never appear in public results.

The public reason array is additive evidence. Clients must not infer priority from its
order. The coordinator sorts it lexically for deterministic output. The primary public
error reason remains explicit in `DomainError.public_reason_code`.

### Canonical Request Fingerprint

The idempotency fingerprint proves semantic identity of admitted caller intent under a
known normalization profile. It is not a signature and does not replace authorization.

Build the fingerprint projection from:

```text
fingerprint_profile             # tokennexus-request-fingerprint-v1
public_contract_major           # 1
scope_id                        # server-derived isolation scope
application_id
task
  content
  content_type
  mandatory_context[]
effective_constraints
cache_directives
```

Exclude these values:

* `idempotency_key` and its hash
* `request_id`, attempt IDs, decision IDs, grant IDs, receipt IDs, and event IDs
* `schema_version` minor and patch values
* Received, recorded, dispatch, completion, lease, and telemetry timestamps
* `traceparent`, `tracestate`, span IDs, and correlation headers
* Actor tokens, raw actor identity, roles that do not affect admitted semantics, and
  credentials
* Policy, pricing, and evaluator versions resolved after admission
* Mutable counters, derived totals, status, receipts, diagnostics, and response data

Roles or jurisdictional claims that change the normalized request must be represented
through a stable server-derived authorization-context fingerprint in the projection.
This must be an allowlisted claim projection, not the access token or complete claims
set.

Fingerprint procedure:

1. Parse the request with duplicate JSON object names rejected.
2. Validate the public contract and authenticated request scope.
3. Materialize defaults and canonical decimal strings using fingerprint profile v1.
4. Apply Unicode NFC to product identifiers and enum-like free identifiers.
5. Preserve user task content bytes after UTF-8 validation and preserve
   order-sensitive arrays.
6. Build the closed fingerprint projection with no unknown fields.
7. Serialize the projection with RFC 8785 JCS.
8. Hash the UTF-8 bytes with SHA-256.
9. Store the lowercase `sha256:<hex>` value with the fingerprint profile.

JCS inherits the I-JSON restriction that JSON numbers must be interoperable IEEE 754
values. Money and quality values are strings specifically to avoid precision loss.
Large counters used in a fingerprint should also be bounded below
`9,007,199,254,740,991` or represented as canonical decimal strings.

### Replay and Conflict Behavior

Admission handles `(scope_id, idempotency_key_hash)` atomically:

| Existing entry | Fingerprint comparison | Result | External work |
| --- | --- | --- | --- |
| None | Not applicable | Create request and in-progress entry | May begin after journal commit |
| In progress | Equal | Return the same request ID and safe current status | No duplicate dispatch |
| Terminal | Equal | Return the stored terminal result | No model, tool, cache mutation, or feedback write |
| Any | Different | Return `conflict` and `request.idempotency_conflict` | None |

An equal replay does not recompute the request under a newer policy. It returns the
original run governed by its frozen policy snapshot. A caller that wants reevaluation
under current policy must use a new idempotency key.

Child operation keys are derived with a domain-separated HMAC or SHA-256 construction
over `request_id`, `attempt_id`, operation kind, and logical operation ordinal. A
transport retry reuses the child key. A quality escalation creates a new attempt and
key. Side-effecting tools must accept an idempotency key or use a local outbox and
receipt protocol. When a remote system cannot provide idempotency or lookup by client
operation ID, an unknown acknowledgement is non-replayable: recovery returns a
controlled failure and requires operator reconciliation rather than repeating the
effect.

Workflow checkpoints may replay pure coordinator transitions. Before any paid or
side-effecting boundary, the recovered coordinator checks the journal for an accepted,
succeeded, failed, or unknown receipt. A receipt marked `unknown` blocks automatic
redispatch.

### Validation Boundaries

| Boundary | Required checks | Failure behavior |
| --- | --- | --- |
| HTTP or client adapter | JSON parse, media type, body size, public schema, duplicate names, authentication | Safe `rejected` response before paid work |
| Admission normalizer | Defaults, decimal and time semantics, scope derivation, policy ceilings, canonical fingerprint | Journal nothing until the normalized request is valid |
| Policy resolver | Snapshot schema, signature or trusted-store provenance, active version, complete reason mapping | Fail closed with no dispatch |
| Coordinator reducer | Legal transition, revision compare-and-swap, terminal immutability, budget and escalation invariants | Reject transition and record internal diagnostic |
| Specialist adapter | Request schema, deadline, reservation, identity, grant references | Do not invoke specialist on mismatch |
| Result adapter | Result schema, identity echo, receipt membership, usage consistency, output/error rules | Quarantine result; coordinator keeps prior state |
| Capability facade | Authorization, grant status, argument schema, deadline, call count, operation idempotency | Deny and write receipt |
| Persistence layer | Unique scoped idempotency key, unique IDs, immutable records, referential integrity, monotonic sequence | Transaction rollback or compare-and-swap conflict |
| Execution projector | Terminal state, ledger reconciliation, required evidence, privacy projection | Do not publish incomplete evidence as complete |
| Public serializer | Public-code allowlist, redaction, status compatibility, response schema | Fail closed to `system.controlled_failure` |

JSON Schema validates local structure: required properties, closed objects, enums,
patterns, numeric ranges, conditional output/error presence, and array uniqueness where
appropriate. Deterministic domain code validates cross-record and temporal facts such
as cost sums, deadline ordering, parent attempts, state transitions, authorization,
and receipt reconciliation. Storage guarantees uniqueness, immutability, ordering, and
atomic journal claims. Adapters validate external acknowledgements and actual usage.

Critical date-time validity must be asserted by parsing and round-trip tests because
Draft 2020-12 treats `format` as annotation unless the implementation explicitly
enables format assertion. Schemas should include both `format: date-time` and the fixed
generation-profile pattern, while domain validation remains authoritative.

### Cross-Record Invariants

The implementation and property-based tests must enforce these invariants:

1. One request has exactly one normalized request fingerprint and policy snapshot.
2. All child records share the admitted request ID and scope.
3. Attempt ordinals are contiguous, unique per request, and never exceed two.
4. Attempt two has attempt one as parent and requires a recorded below-threshold
   evaluation plus an allowed escalation decision.
5. Quality escalation count never exceeds one; transport retries use a separate
   bounded counter.
6. Committed plus active reserved cost, token, and tool allowances never exceed the
   request ceilings.
7. Every paid invocation has a preceding active reservation and durable operation
   key.
8. Every tool receipt references an active, matching, unexpired grant and valid
   authorization decision.
9. A cancellation request or expired absolute deadline prevents every new paid or
   side-effecting operation.
10. A terminal run never returns to a non-terminal state.
11. Late results cannot alter the terminal response or authorize follow-on work.
12. Public results contain only registered public reasons valid for their status.
13. Execution records reconcile exactly with journaled attempts, evaluations,
    reservations, and receipts.
14. Telemetry loss cannot change business state, accounting, authorization, or replay
    behavior.
15. Raw task and response content remain absent from durable records unless an
    explicit, authorized, redacted capture policy enables them.

### Contract Compatibility Policy

Each schema has an independent Semantic Version. The schema URI includes the major
version, for example:

```text
https://schemas.tokennexus.example/contracts/public-request/v1/schema.json
```

The document carries the exact producer version, such as `1.2.0`. A consumer declares
a tested minimum and maximum minor version within one major line.

Compatible minor changes may add optional properties with defaults, add reason codes,
add internal diagnostic codes, or relax a previously rejected value without changing
the meaning of existing data. Patch changes fix documentation, examples, or equivalent
validation expressions.

A major version is required to rename or remove a property, make an optional property
required without a universal default, change a property's type or meaning, change
canonicalization semantics, remove or reuse a reason code, alter money precision, or
change terminal-state semantics.

Closed schemas intentionally reject unknown fields at write boundaries. Rolling
deployments use explicit producer and consumer compatibility ranges, contract fixtures,
and dual-read or dual-write migration adapters when a new minor field must cross mixed
versions. Persisted old records are migrated by a pure, versioned upgrader that retains
the source document and records the migration fingerprint.

### PRD Traceability

| PRD requirement or section | Contract support |
| --- | --- |
| FR-001 Request envelope | `public-request`, admission normalization, UUIDv7 `request_id`, field violations |
| FR-002 Policy routing | `policy-snapshot`, `routing-decision`, stable route reasons, model alias |
| FR-003 Cost estimation and budget action | Money profile, budget reservations, pricing version, budget reasons |
| FR-004 Context optimization | Ordered mandatory context plus before-and-after token facts in execution evidence |
| FR-005 Semantic cache lookup | Cache directives, cache decision reasons, scoped replay-safe cache evidence |
| FR-006 Quality evaluation | `quality-evaluation` with score, threshold, method, version, and unavailable state |
| FR-007 One-step escalation | Attempt parent link, ordinal ceiling, escalation decision and invariant |
| FR-008 Controlled non-escalation | `quality_unmet` plus budget, latency, or policy public reason |
| FR-009 Execution record | Immutable terminal `execution-record` and reconciliation gate |
| FR-010 Baseline comparison | Actual and all-frontier costs plus versioned evidence references |
| FR-011 Policy administration | Immutable policy versions, snapshot fingerprints, later-request activation |
| FR-012 Provider-neutral models | Stable public contracts and product model aliases |
| FR-013 Controlled degraded states | Component statuses, `degraded`, evaluator and telemetry reasons |
| FR-014 Sensitive-content protection | Closed privacy projections, content excluded from hashes and records by default |
| FR-015 User feedback | Separate idempotent feedback reference that cannot mutate routing policy |
| FR-016 Protected-action authorization | Capability grants, authorization decisions, facade checks, denial receipts |
| FR-017 Session and recovery behavior | Stable request ID, journal replay, preserved non-sensitive request workspace |
| FR-018 Compliance evidence catalog | Policy, decision, grant, receipt, execution, and evidence references |
| FR-019 Decision summary | Public decision summary with safe reasons, economics, quality, cache, and escalation |
| FR-020 Bounded tool path | Per-attempt grants, argument schemas, call ceilings, server-side facade |
| NFR-001 and NFR-002 | Secret-free contracts, content persistence off by default, redacted fingerprints |
| NFR-003 | Versioned public reason registry and frozen policy version |
| NFR-004 through NFR-006 | Absolute deadlines, component latency, timeout reasons, bounded outcomes |
| NFR-007 and NFR-008 | Language-neutral schemas and deterministic ports with contract fixtures |
| NFR-010 through NFR-012 | Deny-by-default grants, actionable public errors, hard resource invariants |
| CR-001 through CR-008 | Versioned, immutable, linkable evidence across governance, measurement, privacy, authorization, tool safety, bounds, and transparency |

Primary local evidence:

* `docs/prds/tokennexus-ai-framework-prd.md`, sections 5 through 12
* `.copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md`, API and Schema Documentation and Router-to-Specialist Handoff
* `.copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md`, Typed Handoff Contract through Deterministic Test Strategy

### Considered Alternatives

| Alternative | Decision | Reason |
| --- | --- | --- |
| OpenAPI-only contracts | Rejected | Public HTTP documentation does not cover persisted state, specialist boundaries, journal entries, or cross-record invariants |
| Protobuf as the canonical domain format | Deferred | Strong typing is useful, but JSON Schema aligns with current requirements artifacts and inspectable evidence; adapters may add Protobuf later without changing domain semantics |
| JSON numbers for money and quality | Rejected | Binary floating-point and JCS interoperability can change values across languages |
| Integer micro-units for all money | Deferred | Deterministic but currency scale and pricing precision need product decisions; canonical decimal strings retain explicit values across currencies |
| Random UUIDv4 for all IDs | Acceptable fallback | It is interoperable but loses useful time ordering; UUIDv7 remains opaque and avoids database insertion locality problems |
| Hash the raw request bytes | Rejected | Whitespace, property order, omitted defaults, and equivalent decimals would create false conflicts |
| Hash the complete admitted record | Rejected | IDs, times, trace context, policy versions, and mutable facts would make every replay different |
| Framework checkpoint as idempotency authority | Rejected | Checkpoints may replay transitions and cannot prove whether external paid or side-effecting work occurred |
| Specialist-provided next action | Rejected | It distributes routing, budget, escalation, and authorization authority into probabilistic components |
| One combined public and internal reason registry | Rejected | Operational detail would become a compatibility and disclosure risk |
| Free-form explanation as machine reason | Rejected | Text is unstable, localization-sensitive, and unsafe for client branching |
| Permissive unknown properties | Rejected at trust boundaries | Silent field loss creates downgrade, typo, fingerprint, and policy ambiguity |

### Recommended Source-Document Updates

Update the primary architecture research and PRD during implementation planning rather
than leaving these decisions only in a subagent artifact:

1. Add the selected contract family, JSON Schema dialect, naming convention, and
   independent Semantic Versioning policy to the implementation research.
2. Replace the preliminary specialist shapes with the final identity, operation-key,
   grant-reference, result, and receipt fields.
3. Add the canonical decimal, timestamp, UUIDv7, and fingerprint profiles to an
   architecture decision record.
4. Add the public and internal reason-code governance rules to PRD NFR-003 and the
   decision-summary acceptance criteria.
5. Add exact replay, conflict, in-progress replay, unknown-acknowledgement, and retention
   behavior to FR-001 and FR-017 acceptance criteria.
6. Add journal, receipt, late-result, and terminal-immutability tests to NFR-007 and
   NFR-012 validation.
7. Add a PRD data field for `request_fingerprint`, `policy_snapshot_id`, registry
   version, component statuses, and evidence references.
8. Clarify whether approval is synchronous, asynchronous, or out of scope for MVP, then
   define the corresponding public state and resumption contract.
9. Assign product, FinOps, security, and data-retention owners before freezing schema
   version 1.0.0.

### Planning and Test Deliverables

Implementation planning should create these artifacts in dependency order:

1. Shared JSON Schema primitive definitions and schema registry conventions
2. Public request, result, error, and decision-summary schemas with golden fixtures
3. Policy snapshot, decision, reservation, and quality schemas
4. Specialist request and result schemas plus adapter contract tests
5. Capability grant and operation receipt schemas plus negative authorization tests
6. Idempotency entry and journal storage constraints plus crash-recovery tests
7. Run reducer transition table and property-based invariant tests
8. Execution-record projector, reconciliation checks, and privacy tests
9. Public and internal reason registries with code-to-status validation
10. Version compatibility, migration, canonicalization, and cross-language fixture tests

Golden fingerprint fixtures must include object-property reordering, omitted defaults,
equivalent canonical decimals, Unicode normalization in identifiers, preserved task
content, changed mandatory-context order, changed scope, changed policy-independent
constraints, and excluded trace/timestamp values. At least two implementation languages
must produce identical JCS bytes and SHA-256 outputs before the profile is frozen.

## Recommended Next Research

No additional research is required to begin contract implementation planning. The
following focused validation remains useful before declaring schema version 1.0.0:

* Prototype JCS and decimal fixtures in the first two implementation languages
* Verify the chosen JSON Schema validator supports Draft 2020-12 unevaluated and format
  behavior consistently
* Confirm provider and tool idempotency or operation-lookup capabilities
* Threat-model fingerprint scope, idempotency-key storage, grant resolution, and safe
  Problem Details instances
* Benchmark journal transactions and reducer compare-and-swap behavior against the
  orchestration-overhead target

## Clarifying Questions

These product inputs cannot be resolved from the current PRD or architecture research:

1. Which currencies must MVP support, and is six-decimal pricing precision sufficient?
2. What are the maximum task, context, idempotency-key, and public-response sizes?
3. Which authenticated claims materially affect request semantics and therefore belong
   in the authorization-context fingerprint?
4. Is approval a resumable asynchronous workflow, a blocking response that requires a
   new request, or outside MVP?
5. What retention periods apply to idempotency entries, terminal results, execution
   records, receipts, feedback, and restricted diagnostics?
6. May `quality_unmet` return a bounded output, or must it return metadata only?
7. Which side-effecting product tools are in MVP, and which support native idempotency
   or lookup by client operation ID?
8. Which two implementation languages must pass canonicalization interoperability
   fixtures?
9. What stable HTTPS authority will host schema identifiers and RFC 9457 problem-type
   documentation?
10. Who owns approval of public reason additions and their safe localized messages?
