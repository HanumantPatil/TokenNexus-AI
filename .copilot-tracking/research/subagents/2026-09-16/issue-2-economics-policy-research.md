---
title: Issue 2 Economics and Policy Research
description: Missing behavior, contract shapes, architecture, and tests for GitHub issues 2 and 12 through 14
author: GitHub Copilot
ms.date: 2026-09-16
ms.topic: concept
---

## Research Scope

Research GitHub issue #2 and child issues #12, #13, and #14 against the current
TokenNexus implementation. Scope is limited to `src/tokennexus`, `tests`,
`docs/prds/tokennexus-ai-framework-prd.md`,
`docs/architecture/governed-orchestration.md`, and prior research for domain
contracts and issue #1.

## Research Questions

* What exact behavior is missing?
* What is the smallest architecture consistent with immutable Pydantic contracts,
  coordinator authority, ports, adapters, state, and journal patterns?
* Which public and internal policy, route, budget, reservation, and audit contracts
  are needed?
* Can existing `Coordinator` construction remain compatible?
* Which tests satisfy every child acceptance criterion?
* Which decisions remain ambiguous, and what defaults should implementation adopt?

## Evidence

GitHub issue evidence:

* Issue #2 requires only an eligible and sufficiently funded path to start and every
  route or budget decision to record policy version, estimate, action, and stable
  public reasons.
* Issue #12 requires at least 90 percent expected aliases across at least 30 routine,
  complex, and critical fixtures. Evidence includes alias, policy version, estimate,
  eligibility gates, and stable reasons. Model or specialist recommendations cannot
  override coordinator gates.
* Issue #13 requires at least five over-budget requests to avoid disallowed paid work,
  downgrade only when the cheaper route remains eligible, and atomic reservation of
  cost, tokens, time, and tool allowance before paid model or tool dispatch.
* Issue #14 requires authorized and confirmed valid updates to create a new immutable
  version and audit event. Unauthorized, unconfirmed, and invalid changes preserve
  the active version. Confirmed rollback creates a new auditable transition based on
  a prior approved version.

Local evidence:

* `src/tokennexus/coordinator.py:85-130` admits a request and always starts the first
  attempt with `economical`; there is no policy evaluation before dispatch.
* `src/tokennexus/coordinator.py:289-295` asks the model for an estimate immediately
  before a money-only reservation. It does not persist an admission decision.
* `src/tokennexus/coordinator.py:392-403` similarly reserves only estimated money for
  quality evaluation.
* `src/tokennexus/ports.py:51-63` defines `BudgetPort.reserve` with only request ID,
  operation key, and estimated cost, returning `bool`.
* `src/tokennexus/contracts.py:265-276` exposes no policy version, pre-execution
  estimate, budget action, or eligibility evidence in `DecisionSummary`.
* `src/tokennexus/state.py:40-55` stores no policy snapshot, route decision, or
  reservation evidence in `RunState`.
* `src/tokennexus/journal.py:75-129` stores only run snapshots and terminal results;
  it has no append-only economics or policy-administration records.
* `src/tokennexus/reasons.py:80-111` has allow/block and economical/capable reasons,
  but no downgrade, approval-required, policy-update denial, invalid proposal, or
  rollback reason.
* `tests/orchestration/test_coordinator.py:128-158` proves a routine economical path,
  while `tests/orchestration/test_coordinator.py:287-303` proves only money denial.
  There is no frozen-policy routing corpus or administration suite.
* `docs/architecture/governed-orchestration.md:45-59` preserves coordinator ownership
  and requires reservation before model and quality operations.
* `docs/prds/tokennexus-ai-framework-prd.md:170-180` defines route, budget, and policy
  administration acceptance. Lines 236-241 define the minimum decision and audit
  event payloads. Lines 298-313 require configuration without code changes and a
  tested rollback.
* Prior domain research defines an immutable policy snapshot, route decision,
  multi-dimensional reservation, append-only evidence, stable aliases, canonical
  money, UUIDv7 occurrence IDs, and a closed public reason registry.

## Exact Missing Behavior

1. Admission has no frozen policy snapshot or pricing version.
2. Routing is procedural and fixed, not a deterministic policy decision. High or
   critical requests incorrectly begin on `economical` instead of routing directly
   to `capable`.
3. There is no explicit eligibility evaluation for quality, latency, governance,
   alias availability, or request bounds.
4. Estimates come from one model adapter after the alias has already been chosen.
   The coordinator cannot compare eligible candidates or choose the lowest-cost path.
5. Budget has only allow or deny. Downgrade and approval-required outcomes do not
   exist, and downgrade eligibility cannot be proved.
6. Reservations cover money only, return no receipt, are not journaled, are not
   settled or released, and do not cover token, time, or tool limits.
7. A transport retry reuses the logical operation key. A ledger that deduplicates by
   that key could fail to reserve separately for the second physical paid dispatch.
8. Public terminal decisions omit policy version, pre-execution estimate, budget
   action, and safe eligibility evidence. Blocked results currently have no estimate.
9. No policy repository, authorization boundary, confirmation command, optimistic
   active-version check, immutable policy history, audit event, or rollback exists.
10. Existing model outcomes cannot carry an authoritative route command, which is a
    useful structural protection, but no test proves recommendations are ignored.

## Smallest Consistent Architecture

Keep the application-owned coordinator as execution authority and add one pure policy
domain plus narrow persistence ports.

* Add immutable Pydantic economics contracts to `contracts.py`.
* Add a pure `PolicyEvaluator.evaluate(snapshot, request) -> RouteBudgetDecision` in a
  new `policy.py`. It evaluates all configured aliases from fixed versioned pricing,
  applies quality, latency, governance, and availability gates, sorts eligible paths
  by worst-case cost, and returns one action without invoking dependencies.
* Add `PolicyStore` and `AuditPort` protocols to `ports.py`. The store returns the
  active immutable snapshot, reads approved versions, and atomically creates a new
  active version against an expected current version.
* Replace the money-only reservation input with a `ReservationRequest` covering one
  physical dispatch and cost, input tokens, output tokens, duration, and tool calls.
  Return a `BudgetReservation` receipt. Preserve the logical operation key, but give
  every physical dispatch a distinct reservation ID or dispatch key.
* Extend `RunState` with the frozen snapshot reference, route decision, and immutable
  reservation references. Persist the decision before any paid work.
* Extend `Journal` with append-only decision, reservation, settlement, and audit-event
  operations, or provide a separate evidence journal with the same lock and
  compare-and-set semantics. Do not use telemetry as authoritative evidence.
* Add a small `PolicyAdministrationService`. It validates server-derived actor roles,
  explicit confirmation, proposal semantics, and expected active version before an
  atomic store transition and audit append. It must not route requests or mutate an
  in-flight snapshot.
* Implement in-memory policy, budget-ledger, and audit adapters beside the current
  deterministic substitutes. Keep provider SDK types outside the domain.

The coordinator flow becomes: normalize, resolve a side-effect-free active snapshot,
claim the request with that frozen snapshot, compute and journal one admission
decision, terminalize block or approval-required outcomes, reserve the selected
physical dispatch, then invoke the selected alias. Later quality escalation performs
a new policy and budget gate under the same frozen snapshot.

## Contract Shapes

Public `DecisionSummary` additions:

```text
policy_version: string
pricing_version: string
budget_action: allow | downgrade | approval_required | block
estimated_cost: Money
eligibility_gates: tuple[PublicEligibilityGate, ...]
  gate: quality | latency | governance | availability | budget
  outcome: passed | failed | not_evaluated
model_alias: economical | capable | null
public_reason_codes: sorted unique registered codes
```

Keep `usage` as observed post-dispatch usage. Do not overload it with the admission
estimate. Public eligibility entries expose only gate names and outcomes, not hidden
thresholds, deployment names, prompts, or actor claims.

Internal `PolicySnapshot`:

```text
schema_version, policy_snapshot_id, policy_version, pricing_version
effective_at_utc, supersedes_policy_version, transition_kind
model_policies[]
  alias, enabled, supported_criticalities, maximum_supported_quality
  minimum_latency_ms, governance_labels[]
pricing[]
  alias, input_cost_per_1000_tokens, output_cost_per_1000_tokens
approval_policy, limits, snapshot_fingerprint
```

Internal `RouteBudgetDecision`:

```text
decision_id, request_id, policy_snapshot_id, policy_version, pricing_version
requested_classification, selected_model_alias, budget_action
candidate_estimates[], selected_estimate, eligibility_gates[]
public_reason_codes[], decided_at_utc
```

Internal `BudgetReservation`:

```text
reservation_id, request_id, attempt_id, operation_key, dispatch_ordinal
pricing_version, reserved_cost, reserved_input_tokens, reserved_output_tokens
reserved_duration_ms, reserved_tool_calls, status, created_at_utc
settled_at_utc, actual_usage_reference
```

Policy administration contracts:

```text
PolicyChangeCommand
  expected_active_version, proposal, confirmed

PolicyTransition
  transition_id, transition_kind, source_version, previous_active_version
  new_active_version, actor_id_hash, created_at_utc

PolicyAuditEvent
  event_id, action, actor_id_hash, authorization_outcome, confirmation_outcome
  validation_outcome, previous_version, source_version, resulting_version
  public_reason_codes, recorded_at_utc
```

Actor ID and roles are server-derived method inputs, not trusted fields in the policy
change body. Every denied administration attempt is audited. Invalid and denied
attempts do not create a policy version or alter the active pointer.

## Constructor Compatibility

Preserve all existing keyword-only arguments. Add `policy` and any evidence dependency
as optional keyword-only parameters after `ids`. When omitted, construct a frozen
`pilot-1` in-memory policy that reproduces current standard-request behavior. Existing
call sites continue to build and routine requests remain economical.

This compatibility default is reasonable for one release, but it should be documented
as a local/test default. Production composition must inject a durable policy store and
multi-dimensional budget ledger. Do not make policy globally mutable or hide it in the
model adapter.

## Concrete Test Matrix

### Routing Corpus

Use a checked-in, table-driven corpus of at least 30 labeled cases under one frozen
snapshot. Avoid keyword classification from task prose. Treat fixture `standard` as
routine, `high` as complex, and `critical` as critical unless the product later adds a
separate complexity signal.

* 10 routine cases expected to select `economical`
* 10 complex cases expected to select `capable`
* 10 critical cases expected to select `capable`
* At least four boundary variations in each group across minimum quality, latency,
  token ceilings, and budget
* Assert at least 27 of 30 aliases match and every decision has policy and pricing
  versions, selected estimate, all required eligibility gates, action, and registered
  reasons
* Repeat the corpus twice with frozen IDs and time and assert identical semantic
  decisions and exact call counts
* Inject a model or specialist recommendation for the other alias and assert the
  coordinator-selected alias and gates are unchanged

### Budget and Reservations

Use at least five explicit over-budget cases:

1. Capable is over budget and economical remains eligible: downgrade, then reserve and
   invoke economical only.
2. Capable is over budget and economical fails quality: approval-required or block,
   with zero model calls.
3. Capable is over budget and economical fails governance: approval-required or block,
   with zero model calls.
4. Both aliases exceed cost ceiling: block, with zero model calls.
5. Cost fits but input tokens, output tokens, duration, or tool allowance does not:
   block, with zero paid calls.

For every model attempt, physical retry, paid evaluator, and protected tool fixture,
assert a recorded active reservation exists before dispatch and covers all five
allowance dimensions. Add a race test where two workers compete for the final
allowance and exactly one reservation and dispatch succeeds. Assert settlement cannot
authorize work that failed the pre-dispatch ceiling.

### Policy Administration and Rollback

* Authorized, confirmed, valid update creates one immutable version, one audit event,
  and changes the next request decision, while an in-flight request retains its old
  snapshot.
* Unauthorized update is denied and audited; active version and version count are
  unchanged.
* Authorized but unconfirmed update is denied and audited; active version is unchanged.
* Invalid proposal (unknown alias, negative price, duplicate version, contradictory
  capability, or malformed decimal) is denied and audited; active version is unchanged.
* Stale `expected_active_version` loses compare-and-set and is audited as conflict.
* Confirmed rollback to a prior approved version creates a new immutable version whose
  configuration fingerprint derives from the source version, records source and
  previous active versions, and changes subsequent routing.
* Rollback to a missing, unapproved, or current version is denied and audited.
* Mutation attempts against stored snapshots, decisions, reservations, transitions,
  and audit events fail because all records are frozen.

### Compatibility and Regression

* Existing constructor calls without a policy dependency still execute a standard
  request economically.
* Existing replay, cancellation, deadline, retry, escalation, terminal immutability,
  provider-neutral adapter, contract, and reason tests remain green.
* Exact replay after a policy update returns the original terminal result and does not
  re-evaluate under the new active policy.

## Risks and Recommended Defaults

* Complexity is not a request field. Default `high` to complex and avoid task-text
  heuristics. Add an explicit complexity field only through a future contract version.
* Approval lifecycle is unspecified. Default approval-required to a non-executing
  terminal outcome using `blocked` plus `budget.approval_required`; do not add resumable
  execution in this issue.
* Rollback identity is ambiguous. Never reactivate or mutate an old snapshot. Create a
  new version with `transition_kind=rollback` and `source_version` pointing to the
  approved prior version.
* Fixed-price math needs a rounding rule. Use `Decimal`, worst-case token ceilings,
  round upward to six fractional digits, and reserve pessimistically.
* Availability can make decisions nondeterministic. Freeze alias availability into
  the admission snapshot or a versioned capacity input used by the decision.
* Existing `BudgetPort` compatibility is unsafe if silently retained. Adapt legacy
  money-only ledgers only in tests; production must fail composition unless all
  allowance dimensions and atomicity are supported.
* Audit-write failure ordering is ambiguous. Perform the policy version and audit
  append in one transaction. If that is unavailable, fail closed before changing the
  active pointer.
* Public eligibility evidence can leak policy internals. Expose only closed gate names
  and outcomes; retain thresholds and internal reasons in protected evidence.

## Falsifiable Implementation Hypothesis

If admission freezes one immutable policy snapshot, a pure coordinator-owned evaluator
persists one route-and-budget decision before dispatch, and every physical paid call
has a multi-dimensional atomic reservation, then issues #12 and #13 can be satisfied
without changing model adapters or transferring authority. A separate transactional
policy administration service can satisfy #14 while existing `Coordinator` constructor
calls remain valid through an optional `pilot-1` policy dependency.

The cheapest disproof is one focused coordinator test: submit a `critical` request
under a frozen policy that marks only `capable` eligible, configure the economical
script to fail if called, and assert the first model call is `capable`, a full
reservation precedes it, and the result records policy version, estimate, allow action,
eligibility outcomes, and stable reasons. The current implementation fails this test
because it always dispatches `economical` first and exposes none of that decision
evidence.

## Implementation Sequence

1. Add policy, route, budget, reservation, administration, transition, and audit
   contracts plus closed reason codes and public summary fields.
2. Implement the pure frozen-policy evaluator and the 30-case routing corpus.
3. Add policy-store, audit, and multi-dimensional budget ports with deterministic
   in-memory adapters and atomicity tests.
4. Extend run state and journal evidence, preserving immutable compare-and-set and
   replay behavior.
5. Inject the optional policy dependency into `Coordinator`, evaluate and persist the
   decision before dispatch, and reserve each physical paid call.
6. Add the five over-budget scenarios, downgrade gates, policy-authority tests, races,
   settlement, and replay regression tests.
7. Implement confirmed policy administration and clone-on-rollback with complete
   negative and audit tests.
8. Run the existing contract and orchestration suites, then the full deterministic
   acceptance corpus twice.

## Clarifying Questions

No clarification blocks implementation under the recommended defaults. Product owners
should later decide whether approval-required becomes a resumable public lifecycle,
whether complexity deserves an explicit public field, and which governance labels and
model capability thresholds define the production policy.
