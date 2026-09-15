---
title: Router-to-Specialist Agent Handoff Research
description: Research and MVP recommendation for TokenNexus-AI-Framework router-to-specialist handoff design
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: concept
---

## Research Scope

Investigate router-to-specialist agent handoff approaches for TokenNexus-AI-Framework, grounded in the workspace PRD and relevant repository files.

The research covers:

* Typed handoff contracts
* Centralized versus decentralized orchestration
* Policy and budget enforcement
* One-step escalation
* Correlation and attempt identifiers
* Idempotency
* Cancellation and timeouts
* Protected tools
* Deterministic testing
* Failure semantics
* Avoidance of hidden mutable state
* MVP alternatives and recommendation

## Workspace Evidence

The PRD makes the router an economics and governance control plane, not a
conversation facilitator:

* `docs/prds/tokennexus-ai-framework-prd.md:97-105` limits the MVP to one
  normalized request envelope, one quality-driven escalation, one bounded
  tool or agent path, and deterministic substitutes.
* `docs/prds/tokennexus-ai-framework-prd.md:108-115` excludes multi-agent
  autonomy and unrestricted tool execution.
* `docs/prds/tokennexus-ai-framework-prd.md:152-159` assigns estimation,
  policy evaluation, model selection, quality evaluation, escalation, and
  telemetry recording to one conceptual product flow.
* `docs/prds/tokennexus-ai-framework-prd.md:170-189` requires linked attempts
  under one request ID, no more than one escalation, controlled
  non-escalation, controlled degraded states, independent server-side
  authorization, and a bounded tool path.
* `docs/prds/tokennexus-ai-framework-prd.md:195-206` requires bounded
  dependency timeouts, deterministic substitutes, deny-by-default
  authorization, token and cost ceilings, bounded tool calls, cancellation,
  and timeouts.
* `docs/prds/tokennexus-ai-framework-prd.md:217-229` defines the execution
  record, including policy version, reason codes, quality data, linked attempt
  identifiers, call count, and bounded-path status.
* `docs/prds/tokennexus-ai-framework-prd.md:283-288` names the required
  evidence for prompt and tool protection, consumption bounds, and safe
  transparency.
* `docs/prds/tokennexus-ai-framework-prd.md:315-323` requires end-to-end tests
  for one escalation, budget control, protected actions, and adversarial tool
  use.

The BRD reinforces this boundary:

* `docs/brds/tokennexus-ai-framework-brd.md:151-151` permits at most one
  bounded demonstration tool or agent path.
* `docs/brds/tokennexus-ai-framework-brd.md:160-167` places policy selection,
  quality scoring, escalation, response production, and telemetry in a single
  ordered technical flow.
* `docs/brds/tokennexus-ai-framework-brd.md:180-181` requires one linked
  escalation or a controlled non-escalation outcome.
* `docs/brds/tokennexus-ai-framework-brd.md:186-186` requires a controlled
  response when evaluation or telemetry enrichment fails.
* `docs/brds/tokennexus-ai-framework-brd.md:221-226` requires bounded
  timeouts, deterministic substitutes, and deny-by-default authorization.
* `docs/brds/tokennexus-ai-framework-brd.md:240-241` requires allowlisted,
  argument-constrained tools and bounded model, agent, and tool consumption.

These requirements favor one authoritative orchestration owner. Delegation
may transfer task execution to a specialist, but it must not transfer policy,
budget, escalation, authorization, or final outcome ownership.

## External Evidence

### Microsoft Agent Framework

* [Handoff orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff)
  is decentralized. Agents form a mesh, and the receiving agent takes over
  the task. Context synchronization broadcasts user and agent messages, but
  tool-related content is not synchronized. This is useful for conversational
  ownership transfer, but it does not naturally preserve one authoritative
  economics and policy owner.
* [Agents as tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/)
  keeps a primary agent in control while specialists are exposed as callable
  functions. The primary agent decides when to invoke them and integrates
  their results. This ownership model is closer to the MVP, although an LLM
  should not be trusted to enforce hard policy or budget rules.
* [Workflow concepts](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/)
  describes explicit, inspectable graphs whose typed executors receive values
  through edges. Graph workflows provide type-validated routing, executor
  events, run-scoped state, and checkpointing at superstep boundaries.
* [Agents in workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/agents-in-workflows)
  shows agents adapted into graph executors. Custom deterministic executors
  can therefore own control decisions while an agent performs only the
  specialist step.
* [Human-in-the-loop workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop)
  uses typed request and response channels. A request emits a request ID, the
  workflow pauses, and the response is routed back to the originating
  executor. Pending requests are stored in checkpoints and re-emitted after
  restoration. This supports approval-required actions without keeping an
  in-memory continuation as the source of truth.
* [Workflow checkpoints](https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints)
  persist executor state, pending messages and requests, and shared state.
  Restoring safely requires the same workflow topology and stable agent IDs.
  Checkpoints are a recovery mechanism, not a substitute for a domain
  idempotency journal.
* [Middleware](https://learn.microsoft.com/en-us/agent-framework/agents/middleware)
  can intercept agent, chat, and function calls, share request metadata, and
  terminate execution. It is suitable for telemetry, redaction, and a second
  authorization check. Business policy must still be decided by the
  coordinator before the call.
* [Sequential orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/sequential)
  provides strict ordered processing and can mix agents with deterministic
  executors. Its fixed pipeline is useful, but the MVP needs conditional
  cache, approval, quality, escalation, and degraded-state branches.
* [Concurrent orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/concurrent)
  runs independent agents in parallel. Paying for multiple candidate paths is
  inconsistent with lowest-cost eligible execution in the MVP.
* [Group chat orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/group-chat)
  uses a manager to coordinate iterative multi-agent collaboration and shared
  history. That capability exceeds the single-specialist MVP boundary and
  increases termination and budget complexity.

### Azure Architecture and Microsoft Foundry

* The [Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)
  distinguishes cancellation, immediate retry, and delayed retry, recommends
  bounded attempts, and warns that non-idempotent operations can execute more
  than once when a response is lost. It also recommends placing retry policy
  where the full operation context is understood and avoiding nested retry
  layers.
* [Agent tracing in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/observability/concepts/trace-agent-concept)
  uses OpenTelemetry traces and parent-child spans for workflows, agent
  invocations, model calls, and tool execution. It recommends consistent span
  attributes, correlation with evaluation run IDs, and redaction before
  telemetry export.
* [Microsoft Foundry Toolbox](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/toolbox-overview)
  centralizes tool authentication, authorization, guardrails, observability,
  and version management behind an MCP-compatible endpoint. It can strengthen
  the protected-tool boundary, but some capabilities are preview features and
  direct function calling is not supported through Toolbox.

## Alternatives

| Approach | Control ownership | Fit for one-step MVP | Main limitation | Decision |
| ---------- | ------------------- | ---------------------- | ----------------- | ---------- |
| Native handoff mesh | Receiving agent assumes task ownership | Low | Policy and budget authority become distributed across conversational owners | Reject for MVP |
| Primary agent with specialists as tools | Primary agent retains conversational ownership | Medium | Model-selected tool calls cannot be the sole hard-control mechanism | Use only behind deterministic controls |
| Group chat manager | Manager selects speakers over repeated turns | Low | Shared history and open-ended collaboration add cost and termination complexity | Reject for MVP |
| Sequential orchestration | Pipeline owns a fixed ordered path | Medium | Conditional cache, approval, escalation, and degraded branches are awkward | Reuse concepts, not the complete shape |
| Custom coordinator-owned workflow | Explicit graph and run state own every transition | High | Requires a small domain contract and adapters | Recommend |

Native handoff is not inherently unsafe. It solves a different problem:
interactive transfer of conversational ownership. TokenNexus needs bounded
delegation under a single policy decision, so a custom workflow is the better
semantic match.

Concurrent candidate execution is intentionally excluded. It spends budget
before the platform knows that a second path is necessary and weakens the
product claim that it chooses the lowest-cost eligible path.

## MVP Recommendation

Implement a coordinator-owned custom workflow or state machine with one
specialist invocation adapter. The adapter may wrap a Microsoft Agent
Framework agent as an executor or agent-as-tool, but it receives a restricted
contract and returns a typed result. It cannot select another agent, increase
its budget, authorize tools, change policy, or escalate itself.

### Authoritative Flow

1. The gateway validates and normalizes the public request, then creates one
   immutable `request_id`.
2. The coordinator loads a versioned policy snapshot and derives eligible
   routes, an absolute deadline, cost and token ceilings, and tool grants.
3. The coordinator checks its idempotency journal before any paid or
   side-effecting operation.
4. Cache lookup either produces a final eligible result or routes to attempt
   one.
5. A specialist adapter receives only the task, mandatory context,
   constraints, remaining allowances, and scoped capabilities.
6. The coordinator records the attempt result and runs the versioned quality
   evaluator.
7. If quality is below threshold, the coordinator alone decides whether one
   higher-tier attempt is eligible. It creates attempt two with
   `parent_attempt_id` set to attempt one.
8. The coordinator maps success, degraded behavior, denial, cancellation, or
   failure to a stable public result and writes the execution record.

Quality escalation and transient retry must remain distinct. An escalation is
a second model attempt on a higher eligible tier and consumes the single
escalation allowance. A transport retry repeats the same operation only for an
allowlisted transient failure and must follow a separate, smaller retry
policy. Both consume the same request deadline and budget. Neither specialist
nor provider SDK may add an unobserved retry layer.

### Typed Handoff Contract

The contract should be a versioned domain type rather than a free-form chat
transcript. The following language-neutral shape identifies the minimum MVP
fields:

```text
SpecialistRequest
  schema_version
  request_id
  attempt_id
  parent_attempt_id?
  attempt_ordinal                 # 1 or 2
  idempotency_key
  specialist_kind
  task
  mandatory_context[]
  declared_constraints
  policy_version
  route_reason_codes[]
  absolute_deadline_utc
  remaining_budget
    max_cost
    max_input_tokens
    max_output_tokens
    max_tool_calls
  escalation_count               # 0 or 1
  capability_grants[]
    tool_name
    allowed_operation
    argument_constraints
    authorization_decision_id
  trace_context
    traceparent
    tracestate?

SpecialistResult
  schema_version
  request_id
  attempt_id
  status
  output?
  usage
    input_tokens
    output_tokens
    estimated_cost
    provider_latency_ms
    tool_call_count
  tool_receipts[]
  specialist_reason_codes[]
  retry_classification           # none, transient, or terminal
  error?
    code
    safe_message
    component
```

The coordinator validates identity fields on return and rejects a result whose
`request_id`, `attempt_id`, schema version, or allowance receipts do not match
the dispatch record. Specialists return facts and classifications. They do not
return an authoritative next route.

### Correlation and Attempt Identity

Use identifiers with separate meanings:

* `request_id` is stable across the entire client operation, cache decision,
  both quality attempts, evaluation, and final response.
* `attempt_id` is unique for each paid model invocation. Attempt one and the
  optional escalation each receive a distinct value.
* `parent_attempt_id` links only the escalation to the below-threshold attempt
  that caused it.
* `attempt_ordinal` is constrained to 1 or 2, and `escalation_count` is
  constrained to 0 or 1.
* W3C `traceparent` carries runtime span correlation. It does not replace the
  business identifiers stored in the execution record.
* Approval request IDs and tool call IDs remain distinct child-operation
  identifiers linked to the relevant attempt.

### Policy and Budget Enforcement

Enforcement belongs in deterministic coordinator executors at every costly or
side-effecting transition:

* Freeze one immutable policy snapshot at request admission and record its
  version. A mid-request policy update applies only to later requests.
* Calculate eligibility and reserve estimated cost before dispatch. Reconcile
  actual usage after completion and carry only the remaining allowance to the
  next transition.
* Derive every child deadline from the minimum of the request deadline and the
  component-specific timeout. Never reset the parent deadline during retry,
  approval resume, or checkpoint restore.
* Reject a second escalation transition structurally. Do not rely on prompt
  wording to enforce the limit.
* Count tool calls at the server-side capability facade, not from model output
  alone.

Middleware should independently verify the dispatch identity, remaining
allowance, capability grant, and telemetry context immediately before model or
tool execution. A mismatch terminates the call. This check is defense in depth
and protects against adapter defects; the coordinator remains the business
decision authority.

### Idempotency and Recovery

Use a durable idempotency journal keyed by authenticated application scope and
`idempotency_key`. Store the normalized request hash, run status, dispatch
receipts, attempt results, and terminal response reference.

* A replay with the same key and request hash returns the recorded in-progress
  or terminal state without creating another paid attempt.
* A replay with the same key and a different hash returns a conflict.
* Each provider invocation and side-effecting tool call receives a stable
  child operation key derived from `request_id`, `attempt_id`, operation name,
  and operation ordinal.
* A recovered coordinator checks the journal before resending an operation
  whose acknowledgement was lost.
* Framework checkpoints may restore graph progress and pending approvals, but
  the journal remains authoritative for duplicate suppression and accounting.

For a hackathon implementation, the journal can be a transactional local
store. The contract and tests should not assume in-process memory so that the
storage implementation can be replaced later.

### Cancellation and Timeouts

Cancellation flows from the gateway to the coordinator and every adapter or
tool call. Each boundary checks cancellation before reserving budget, before
dispatch, and after an awaited operation returns.

* A client cancellation prevents new attempts and tool calls.
* A deadline expiry is a terminal routing decision, even if a late dependency
  result arrives.
* Late results may be recorded for operations analysis but cannot overwrite a
  terminal cancelled or timed-out response.
* Approval-required operations expire with the request deadline. Resuming an
  expired approval cannot reopen the run.
* Cleanup and telemetry flushing use a small independent shutdown allowance,
  but cannot trigger business operations.

### Protected Tools

Do not expose a broad tool registry directly to the specialist. Provide a
per-attempt capability facade containing only approved product operations.
Validate authorization, arguments, call count, deadline, and idempotency at
that facade. Require an explicit external approval request for configured
high-impact operations.

Foundry Toolbox can later centralize credentials, tool versions, guardrails,
and observability. For the MVP, a small local allowlist and server-side adapter
is sufficient and easier to test deterministically. The client UI and prompt
are not enforcement boundaries.

### Failure Semantics

Return one terminal public status and retain detailed component evidence in
the execution record. Public reason codes should be allowlisted and stable.

| Condition | Public status | Retry or escalation behavior |
| ----------- | --------------- | ------------------------------ |
| Invalid contract or constraint | `rejected` | No dispatch |
| Policy, budget, or authorization denial | `blocked` | No retry; escalation forbidden |
| Duplicate key with different payload | `conflict` | No dispatch |
| Client cancellation | `cancelled` | Stop new work; ignore late success |
| Absolute deadline exceeded | `timed_out` | Stop new work; ignore late success |
| Specialist unavailable before output | `failed` or `degraded` | Bounded transient retry only when policy permits |
| Evaluator unavailable after valid output | `degraded` | Return controlled output; do not guess that escalation is required |
| Quality below threshold, escalation allowed | Pending until attempt two | Exactly one linked escalation |
| Quality below threshold, escalation forbidden | `quality_unmet` | Return budget, latency, or policy reason |
| Telemetry enrichment unavailable | `degraded` | Preserve routine result and mark component status |
| Tool denied or argument invalid | `blocked` | No alternate tool chosen by specialist |
| Replay of completed identical request | Recorded terminal status | Return prior result without new side effects |

Provider exceptions and stack traces are internal evidence. They must not be
copied into the public reason or model context. Record whether a component
failure was transient or terminal so retry policy remains deterministic.

### Avoiding Hidden Mutable State

Pass one explicit `RunState` value through coordinator transitions. It should
contain the immutable request and policy snapshot plus append-only decisions,
reservations, receipts, attempt summaries, evaluator outcomes, and terminal
status.

* Do not store request policy, counters, budgets, cancellation state, or
  authorization decisions in module globals, singleton agents, prompts, or
  mutable chat history.
* Do not let specialists share writable memory or communicate outside the
  coordinator contract.
* Inject clocks, ID generators, pricing, policy stores, providers, evaluators,
  caches, tool facades, journals, and telemetry sinks.
* Reset or recreate framework executors between independent runs unless their
  state is explicitly run-scoped and checkpointed.
* Treat telemetry as an observation sink, never as the authoritative state
  used to decide the current request.

### Deterministic Test Strategy

Use fake clocks and ID generators plus scripted substitutes for the model,
evaluator, cache, pricing, approval port, tools, journal, and telemetry sink.
Assert both the final result and the ordered transition or receipt log.

Minimum architecture tests should prove:

1. A routine request invokes one economical specialist and no other path.
2. A seeded low score creates exactly two distinct attempts under one request
   and links the second to the first.
3. A second low score cannot create attempt three.
4. Budget or latency exhaustion after attempt one prevents escalation before
   another provider call.
5. A duplicate identical request produces no additional model or tool call.
6. Reusing an idempotency key with changed input returns a conflict.
7. Cancellation before dispatch produces no reservation or provider call.
8. Cancellation or timeout during a call prevents a late result from changing
   the terminal state.
9. A restored checkpoint re-emits an approval request without repeating the
   protected operation.
10. A specialist cannot call an ungranted tool or exceed argument and call
    bounds.
11. An evaluator outage returns the configured degraded result and records the
    component state.
12. Repeating the frozen suite produces identical route, policy, reason-code,
    escalation, and tool-authorization outcomes.

Property-based tests can generate budget, deadline, and escalation states and
assert invariants: total reserved cost never exceeds the ceiling, attempt
ordinal never exceeds two, escalation count never exceeds one, terminal state
never reopens, and ungranted tools are never invoked.

## Remaining Gaps

The architecture recommendation does not depend on the following open product
choices, but implementation values do:

* The application language and the selected Microsoft Agent Framework SDK
* The reference specialist domain and its exact typed task and output payloads
* The two model tiers, provider retry behavior, and whether SDK retries can be
  disabled or surfaced
* The evaluator rubric, threshold, and evaluator-unavailable policy
* Cost, token, latency, and tool-call ceilings
* The list of protected product tools and operations requiring approval
* The durable store selected for idempotency and checkpoint persistence
* The public error and reason-code catalog
* The treatment of requests already executing when an authorization grant is
  revoked

## Suggested Next Research

* Define JSON Schema or native SDK types for `SpecialistRequest`,
  `SpecialistResult`, `RunState`, and the execution record
* Prototype one custom graph with a deterministic specialist, approval port,
  journal, and injected clock
* Verify provider retry configuration and cancellation propagation for the two
  chosen model adapters
* Threat-model the capability facade and toolbox option against the selected
  specialist and protected tool
* Benchmark coordinator overhead against the 500 ms p95 PRD target
* Freeze the failure-code catalog and map every code to client copy and
  telemetry fields

## Key Findings

* The MVP should use centralized control with bounded specialist delegation,
  not decentralized conversational handoff.
* A custom Agent Framework workflow is the strongest fit because typed
  executors and explicit edges can make policy, budget, escalation, approval,
  and terminal-state transitions inspectable and testable.
* Agents-as-tools is a useful invocation adapter, but deterministic code must
  decide whether a specialist or tool call is allowed.
* One request ID, distinct attempt IDs, child operation IDs, and W3C trace
  context provide complementary business and runtime correlation.
* Checkpointing supports recovery; a separate idempotency journal prevents
  duplicate paid calls and side effects.
* Middleware, approval-required tools, and Foundry Toolbox strengthen the
  boundary but do not replace coordinator-owned business policy.
* Explicit run state and injected dependencies are necessary for deterministic
  tests and to avoid hidden mutable state in reusable agents or processes.
