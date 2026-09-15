---
title: Bounded Agent and Protected Tool Threat Model Research
description: Threat model and MVP control recommendation for the TokenNexus-AI-Framework bounded specialist and protected-tool path
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: concept
---

## Research Status

Status: Complete

## Research Questions

* What trust boundaries and threats govern the bounded specialist and protected-tool path?
* Which capability grants, enforcement order, approvals, revocation semantics, audit evidence, and degraded behaviors are required?
* Which deterministic adversarial tests prove the controls?
* Should the MVP use an application-owned capability facade or Foundry Toolbox and MCP?

## Working Hypothesis

Use an application-owned capability facade as the MVP policy enforcement point. Treat Microsoft Foundry Toolbox or an MCP server as a downstream tool transport and management boundary only when its benefits justify the added identity, protocol, supply-chain, and availability surface.

## Findings

### Executive conclusion

The hypothesis is supported. TokenNexus should implement one application-owned capability facade between every specialist and every protected tool. A specialist may propose a typed tool call, but it must not authorize, credential, or directly execute that call. The coordinator remains the authority for task state and budgets; the facade independently performs execution-time authorization against a signed, task-scoped grant and the current policy snapshot.

Microsoft Agent Framework provides useful implementation primitives for this design: explicit workflows, function-call middleware that can inspect or block calls, typed human-in-the-loop requests, and checkpoint restoration. Microsoft Foundry Toolbox provides a managed MCP-compatible endpoint, centralized credentials, guardrails, observability, and tool versioning. These are complementary downstream facilities. Neither is a substitute for TokenNexus's request-level grant evaluator because neither owns TokenNexus task identity, attempt limits, quality-escalation state, cost budgets, or business-specific impact policy.

This design directly supports the PRD's bounded agent and tool path, deny-by-default protected tools, request-scoped resource limits, deterministic substitutes, data minimization, complete execution records, and controlled degradation. The controlling local evidence is in:

* docs/prds/tokennexus-ai-framework-prd.md
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md
* .copilot-tracking/research/subagents/2026-09-15/conversation-memory-research.md

### Scope and assumptions

The threat model covers the path from an authenticated TokenNexus request through coordinator routing, specialist execution, capability authorization, optional human approval, protected-tool invocation, result validation, and audit. Model-provider inference without a protected side effect remains governed by the separate model-routing and budget policy, although prompt injection and resource limits cross both paths.

Assumptions:

* The coordinator is trusted to derive task intent and issue grants, but its output is still treated as untrusted input at the facade.
* Specialists, model output, retrieved content, memory, tool metadata, tool arguments, and tool results are untrusted.
* A protected tool can read sensitive data, create an external side effect, spend material resources, cross a tenant boundary, or alter security-relevant state.
* Human approval is an authorization input for one disclosed operation, not a delegation of open-ended authority.
* Raw prompts and full tool results are not persisted by default. Audit evidence uses identifiers, classifications, hashes, counts, decisions, and redacted summaries.
* Grants are per task attempt. Retry, escalation, and resumed workflow execution do not implicitly broaden or renew them.
* Tool identity means the immutable combination of registry namespace, tool name, semantic operation, implementation version or digest, and schema digest. A display name alone is insufficient.

### Assets and security objectives

| Asset | Security objective |
|---|---|
| User and workload identity | Preserve authenticated subject, tenant, audience, and delegation chain without token passthrough. |
| Capability grants | Prevent forgery, replay, widening, substitution, and use outside the bound task attempt. |
| Policy and tool registry | Preserve approved policy version, tool identity, schema, impact classification, and revocation state. |
| Secrets and credentials | Keep credentials out of prompts, specialist state, tool arguments, results, and logs; mint only audience-bound, short-lived credentials at execution. |
| Request and memory context | Prevent injected or retrieved content from changing identity, grants, policy, budget, or approval state. |
| External systems and data | Prevent unauthorized reads, writes, disclosure, deletion, spending, and cross-tenant access. |
| Budget and service capacity | Bound calls, tokens, time, concurrency, retries, payload size, and financial exposure. |
| Audit journal | Provide attributable, ordered, tamper-evident evidence for every proposal, decision, approval, execution, result, denial, timeout, and revocation. |
| Tool results | Preserve provenance and prevent untrusted output from becoming executable instructions or privileged context. |

### Actors and trust boundaries

| Actor or component | Trust posture | Allowed authority |
|---|---|---|
| End user or calling workload | Authenticated but not inherently authorized | Submit a request within assigned product permissions. |
| Coordinator | Trusted control-plane component | Route work, own task state and budgets, and request a bounded grant from policy. It cannot bypass the facade. |
| Specialist agent | Potentially compromised execution unit | Produce typed facts and propose calls covered by an attached grant reference. It cannot hold reusable credentials or mutate policy. |
| Capability policy service | High-trust deterministic component | Evaluate identity, task, operation, resource, budget, impact, and policy version; issue or deny signed grants. |
| Capability facade | High-trust policy enforcement point | Reauthorize every call, obtain approval, mint credentials, invoke tools, validate results, meter use, and journal evidence. |
| Human approver | Authenticated decision maker | Approve or deny the exact disclosed operation if authorized for its impact class and scope. |
| Tool registry | High-trust configuration source | Resolve pinned tool and schema digests, impact class, data class, and allowed transport. |
| Foundry Toolbox or MCP server | Downstream service, not policy authority | Host and invoke approved tools under a facade-issued identity and constrained request. |
| Protected tool or external service | Untrusted response and failure boundary | Perform only the authorized operation and return a bounded result. |
| Memory, retrieval, cache, and model provider | Untrusted content sources | Supply data; never supply authority. |
| Audit and telemetry pipeline | High-integrity evidence sink | Receive redacted structured events; it cannot authorize execution. |

The critical boundaries are: caller to coordinator, coordinator to specialist, specialist to facade, facade to approval service, facade to credential broker, facade to Toolbox or MCP, tool result back to facade, and operational events into the audit sink. Network placement and managed identity strengthen these boundaries but do not replace per-call authorization.

### Threat matrix

| ID | Threat and attack path | Required controls | Failure behavior |
|---|---|---|---|
| T01 | Direct or indirect prompt injection causes a specialist to reinterpret untrusted content as authority. | Separate instructions from data; mark provenance; prohibit identity, policy, budget, grant, and approval mutation from model or retrieved output; deterministic facade authorization. | Deny the call, classify the injection signal, and continue without tools only when a safe non-tool result is possible. |
| T02 | Confused deputy uses TokenNexus authority for a caller or resource the caller cannot access. | Bind grant to tenant, subject, actor, task, attempt, audience, operation, resource selectors, and purpose; recheck caller entitlement and resource ownership at execution. | Deny without credential minting; journal caller and resource hashes plus reason code. |
| T03 | Specialist escalates privilege by choosing a broader tool, operation, resource, or data scope. | Deny-by-default allowlist; exact operation and parameter constraints; registry-pinned semantic identity; no wildcard resources for side-effecting tools. | Deny and invalidate the attempt if repeated or clearly malicious. |
| T04 | Grant replay or duplicate delivery repeats a side effect. | Signed grant ID, nonce, attempt binding, expiry, maximum-use count, idempotency key, atomic consume-before-execute ledger, and tool-side idempotency where available. | Return the recorded prior receipt for the same canonical request; deny mismatched reuse. |
| T05 | Excessive agency chains tools, delegates further, or turns a read into an unbounded workflow. | Specialists cannot mint grants or delegate; cap tool count and chain depth; classify read/write/delete/spend/administrative impact; one explicit coordinator step per protected call. | Stop at the current boundary and return a typed policy denial or budget exhaustion result. |
| T06 | Compromised or rogue specialist fabricates task state, approval, or tool receipts. | Facade accepts only coordinator-issued task identity and policy-service signatures; approval and execution receipts originate from dedicated services; specialists return facts, not authoritative state. | Reject invalid provenance and quarantine the specialist version from further protected calls. |
| T07 | Tool or schema poisoning changes a descriptor so destructive behavior appears benign. | Approved registry, immutable version and schema digests, signed release metadata, change review, semantic impact classification independent of tool annotations, and runtime digest comparison. | Fail closed on missing, changed, or unclassified metadata. |
| T08 | Command, path, query, URL, template, or argument injection reaches an interpreter or downstream service. | Structured APIs; schema plus semantic validation; canonical resource identifiers; parameter allowlists; reject shell fragments and unsafe URI schemes; sandbox unavoidable interpreters. | Deny before invocation and redact the rejected value in telemetry. |
| T09 | Unsafe tool output is rendered, executed, persisted, or injected into a later prompt as trusted instructions. | Treat all results as data; validate response schema, type, size, encoding, content type, provenance, and data classification; escape at sinks; summarize or tokenize before model reuse. | Quarantine invalid output, emit a bounded error, and never pass raw output to another privileged operation. |
| T10 | Memory, cache, or retrieved context poisons future calls or crosses tenant/user/use-case boundaries. | Ephemeral task state by default; partition cache and retrieval by tenant, user, use case, policy, model, and tool version; retrieved memory cannot alter authority; TTL and deletion support. | Bypass suspect memory or cache and continue from trusted request state; deny if required context cannot be reconstructed safely. |
| T11 | Secret leakage occurs through prompts, delegated tokens, arguments, results, checkpoints, logs, or exceptions. | No token passthrough; credential broker mints short-lived audience-bound credentials after approval; secret references instead of values; redaction and data-loss checks on every boundary. | Stop and revoke affected credentials; suppress sensitive payloads and create a security event. |
| T12 | Resource exhaustion consumes token, tool, network, storage, concurrency, or financial budgets. | Absolute deadline; per-task and per-tool call, byte, row, token, duration, concurrency, retry, and spend limits; circuit breakers; server-side pagination; bounded output. | Cancel in flight where supported, revoke grant, and return a controlled budget or deadline result. |
| T13 | Approval manipulation hides impact, mislabels the resource, or changes arguments after approval. | Approval view is generated from canonical validated arguments and pinned tool metadata; bind approval receipt to request digest; any material mutation requires new approval. | Deny digest mismatch and discard stale approval. |
| T14 | Approval fatigue trains users to approve repetitive or opaque requests. | Approve only high-impact operations; concise disclosure of action, target, data, cost, and reversibility; no bundled unrelated actions; rate limit prompts; no preselected approval; allow deny and inspect. | Time out to denial. Repeated prompts trip a task-level circuit breaker rather than relaxing control. |
| T15 | Revocation failure lets queued, retried, resumed, or in-flight calls execute after access is removed. | Check revocation immediately before credential mint and dispatch; short expiry; cancel queued work; propagate revocation epoch; downstream token lifetime shorter than grant lifetime. | Prevent new dispatch immediately; best-effort cancel in-flight work; reconcile and alert if the external side effect may have occurred. |
| T16 | Audit gaps prevent attribution or let a specialist forge a success. | Append-only ordered events with trusted timestamps, actor chain, request and policy digests, grant and approval IDs, tool digest, meter values, reason codes, and signed execution receipt. | Treat missing authorization, dispatch, or terminal evidence as `outcome_unknown`, not success; block dependent side effects. |
| T17 | Cascading failure causes retry storms, duplicate side effects, stale policy use, or unsafe fallback. | Single retry owner; idempotency; circuit breakers; absolute deadlines; bounded queues; bulkheads; no fallback to a more privileged tool or credential; pinned policy version with revocation overlay. | Degrade to deterministic or non-tool behavior where valid; otherwise fail closed with a typed terminal result. |
| T18 | MCP token theft, audience confusion, or passthrough lets a server reuse upstream credentials. | OAuth resource/audience binding, separate downstream token, least scopes, TLS, secure token storage, and explicit prohibition on token passthrough. | Reject invalid audience or resource indicators and do not forward the caller token. |
| T19 | Shadow or substituted MCP server impersonates an approved endpoint. | Registry-pinned HTTPS origin, certificate validation, private endpoint where required, server identity verification, deployment digest, allowlisted redirects, and configuration change control. | Fail closed on identity or origin mismatch. |
| T20 | Human approver or administrator abuses legitimate access. | Separate approver roles by impact and tenant; least privilege; dual control for irreversible or security-administrative actions; immutable audit; periodic access review. | Deny absent separation-of-duty evidence; alert on anomalous approvals. |

### Capability grant contract

The grant is an authorization artifact, not an access token and not model-visible authority. Persist only the minimum fields required for verification and audit. A representative contract is:

```yaml
grant_id: uuidv7
grant_version: 1
issuer: tokennexus-policy
tenant_id: tenant-reference
subject_id: caller-reference
actor_id: coordinator-reference
specialist_id: specialist-reference
task_id: task-reference
attempt_id: attempt-reference
purpose: normalized-task-purpose
policy_version: immutable-policy-version
revocation_epoch: integer
tool:
	namespace: approved-registry
	name: canonical-tool-name
	operation: canonical-operation
	version: immutable-version
	implementation_digest: sha256-digest
	request_schema_digest: sha256-digest
	response_schema_digest: sha256-digest
	audience: downstream-resource-indicator
constraints:
	resource_selectors: []
	parameter_constraints: {}
	data_classes: []
	network_destinations: []
	max_uses: 1
	max_input_bytes: integer
	max_output_bytes: integer
	max_duration_ms: integer
	max_cost: decimal-string
	currency: ISO-4217-code
	requires_approval: true
	approval_class: high-impact
issued_at: RFC-3339-UTC
not_before: RFC-3339-UTC
expires_at: RFC-3339-UTC
nonce: random-value
signature: detached-signature-reference
```

Contract rules:

* Sign a canonical representation and verify it locally at the facade. Do not sign or log secrets.
* `tenant_id`, `subject_id`, `task_id`, and `attempt_id` must be exact matches, not caller-supplied defaults.
* Resource selectors and parameter constraints narrow authority. Runtime arguments must be a subset; they cannot amend the grant.
* `max_uses` defaults to one. A read-only operation may permit more only when policy states an explicit bounded count.
* Approval binds to the canonical call digest, grant ID, approver identity, approval policy version, and expiry.
* Policy pinning guarantees reproducibility, while an independently checked revocation overlay permits emergency denial without rewriting history.
* Credentials are minted separately after final authorization. The grant must never be accepted by the downstream tool as a bearer credential.

### Enforcement order

Complete mediation requires the same ordered checks for first execution, retry, resumed checkpoint, and quality escalation:

1. Authenticate the caller or workload and derive tenant, subject, actor, assurance, and delegation facts from trusted identity infrastructure.
2. Load coordinator-owned task state, absolute deadline, attempt counters, consumed budgets, cancellation state, and immutable policy reference.
3. Parse the specialist proposal as data and validate its contract, provenance, size, and task or attempt binding.
4. Verify grant signature, issuer, audience, subject and actor chain, time window, nonce, revocation epoch, remaining uses, and budget ceilings.
5. Resolve the tool from the approved registry and compare operation, implementation version or digest, request and response schema digests, origin, and impact class.
6. Canonicalize and validate arguments against both the schema and semantic policy: resource ownership, tenant boundary, parameter constraints, destination allowlist, data classification, and purpose.
7. Reauthorize against current caller entitlements, revocation overlay, remaining task and tool budgets, concurrency limits, and service health. This check is deterministic and independent of model confidence.
8. If policy requires approval, generate a disclosure from the pinned metadata and canonical arguments; verify the approver's role and bind the signed decision to the exact call digest. Mutation after approval returns to step 6.
9. Atomically reserve budget and consume the grant or idempotency slot. A duplicate canonical call returns the existing receipt or an `outcome_unknown` state; it does not dispatch again.
10. Mint a short-lived, least-privilege, audience-bound downstream credential. Never forward the caller's bearer token or expose credentials to the specialist.
11. Execute through an isolated adapter with network allowlists, timeout, payload and result bounds, cancellation, rate limits, and circuit breaker. Toolbox or MCP may be used here.
12. Validate, classify, redact, and size-limit the result before any rendering, storage, model reuse, or subsequent tool proposal.
13. Commit the execution receipt, metering, external operation identifier, result digest, terminal status, and reason code to the append-only journal; release unused reservation and revoke ephemeral credentials.
14. Return a typed result to the coordinator. Only the coordinator updates task progression, retry, escalation, or user-facing outcome.

No step may be skipped because an upstream component already performed a similar check. Defense in depth is intentional, but only the facade is the execution policy enforcement point.

### Approval policy

Approval should be based on impact, not on whether a model requested the operation. Safe reads of low-classification data can be preauthorized by a narrow grant. Approval is mandatory for writes to external systems, deletion, publication, communication to third parties, material spending, access to high-classification data, security or identity administration, cross-tenant movement, and any operation whose impact cannot be classified deterministically.

The approval disclosure must show:

* Exact action and canonical target.
* Tenant or account boundary.
* Data classification and fields disclosed or modified.
* Expected cost or bounded maximum.
* Whether the action is reversible and the rollback mechanism.
* Why the operation is needed for this task.
* Grant expiry and whether this is a retry or prior unknown outcome.

Approvals are single-operation and short-lived. Batch approval is allowed only for a homogeneous, enumerated set with one impact class and a bounded item count. Irreversible, security-administrative, or unusually high-cost operations require a stronger approver role or dual control. Absence, timeout, cancellation, stale policy, changed arguments, or unknown prior outcome all resolve to denial.

Anti-fatigue controls include prompt rate limits, deduplication, aggregation of homogeneous low-risk items, an explicit no-approval path for denied work, no dark patterns or default approval, and task termination after repeated approval requests. The system must never lower an approval requirement because requests are frequent.

### Revocation semantics

Immediate revocation applies to queued and not-yet-dispatched work. Increment a revocation epoch or record the grant ID in a strongly consistent deny set, recheck it immediately before budget consumption and dispatch, cancel pending approvals, invalidate queued jobs, and prevent credential minting. Emergency tool, specialist, tenant, subject, or policy revocation must also be expressible without enumerating every grant.

In-flight external side effects cannot always be recalled. TokenNexus should attempt cancellation, expire the short-lived credential, mark the attempt `revocation_requested`, and reconcile using the downstream operation ID. Until a signed terminal receipt or authoritative reconciliation exists, the outcome is `unknown`; dependent side effects remain blocked. This distinction prevents a false claim of immediate revocation after an irreversible dispatch.

Eventually consistent revocation is acceptable only for already dispatched read-only work whose results are quarantined until a final revocation check. It is not acceptable for credential minting, writes, deletion, spending, or security administration.

### Audit evidence

The audit journal should record structured events rather than raw content. Required event families are proposal received, grant issued or denied, execution authorization allowed or denied, approval requested or decided, budget reserved or rejected, credential minted by reference, dispatch started, downstream acknowledged, result validated or quarantined, execution completed, timeout or cancellation, revocation, reconciliation, and final coordinator outcome.

Every event should carry:

* Trace, request, task, attempt, proposal, grant, approval, idempotency, and execution receipt identifiers as applicable.
* Tenant, subject, actor, coordinator, specialist, facade, approver, and downstream service references.
* Policy version, revocation epoch, tool operation, implementation digest, schema digests, and adapter version.
* Canonical request digest, redacted resource digest, data and impact classifications, and result digest.
* Decision, stable reason code, timestamps, deadline remaining, use count, retry or escalation counter, and budget reservation or consumption.
* Downstream operation ID, HTTP or protocol status class, terminal certainty, and reconciliation state.

Use an append-only sink with restricted writers, trusted server timestamps, retention policy, access logging, integrity protection, and alerting for sequence gaps. Store secrets, bearer tokens, raw prompts, unrestricted arguments, and raw high-classification results nowhere in this journal. A support view can resolve approved references under separate authorization.

### Fail-closed and degraded behavior

Fail closed for invalid identity, signature, audience, grant binding, registry identity, schema digest, semantic authorization, approval, revocation status, side-effect idempotency, credential minting, or audit precondition. There is no fallback to a broader tool, shared credential, unapproved MCP server, or more privileged specialist.

Controlled degradation is allowed when the user can still receive a truthful bounded result without the protected operation:

* Return deterministic cached or static guidance when its scope, policy, and provenance are valid.
* Return a non-tool specialist answer clearly marked as incomplete when no external fact or side effect is implied.
* Queue no work when authorization or approval is unavailable; expose a retryable typed status only for transient infrastructure failure.
* Open circuit breakers and shed low-priority work when Toolbox, MCP, or a downstream service is unhealthy.
* Quarantine tool results when result validation or audit export is unavailable.

An audit exporter outage may buffer integrity-protected events only within a fixed local bound. Once that bound is reached, protected writes fail closed. Protected operations must never become unaudited to preserve availability.

### Deterministic adversarial tests

Use fake clocks, deterministic identities, an in-memory atomic grant ledger, signed fixture grants, fixed policy and registry snapshots, fake credential broker, fake approval service, and stub tools. Assert both the returned reason code and the absence or exact count of downstream invocations.

| Test | Expected invariant |
|---|---|
| Inject instructions through user input, retrieved text, memory, cache, tool description, and tool result. | No content source can alter identity, grant, policy, budget, approval, or tool registry state. |
| Change tenant, subject, task, attempt, purpose, resource, operation, audience, or specialist after grant issuance. | Facade denies before credential minting and dispatch. |
| Reuse a consumed grant concurrently from two workers. | Atomic ledger permits at most one dispatch; the duplicate receives the same receipt or a stable replay denial. |
| Replay with the same idempotency key but different canonical arguments. | Facade denies the mismatch and does not return the prior result. |
| Change tool implementation, schema, origin, impact classification, or annotations after approval. | Digest or registry mismatch fails closed and invalidates approval. |
| Supply shell metacharacters, traversal paths, unsafe URLs, query fragments, oversized arrays, recursive JSON, or disallowed destinations. | Validation denies without invoking the adapter. |
| Return HTML, script, prompt instructions, secrets, wrong schema, wrong content type, excessive bytes, or cross-tenant data. | Result is quarantined and never rendered, persisted, or reused as trusted context. |
| Forward a caller token to the MCP server or mint a token with the wrong audience or excessive scopes. | Credential broker or facade rejects; no downstream request is sent. |
| Approve a call and then mutate any material argument. | Approval digest mismatch forces a new decision. |
| Flood approval requests or let approval expire. | Requests deduplicate and rate-limit; expiry and no response deny; requirements never weaken. |
| Revoke before approval, before dispatch, during dispatch, and before result release. | Pre-dispatch cases invoke nothing; in-flight case records unknown or reconciled outcome; revoked read result is withheld. |
| Exhaust each call, byte, row, duration, concurrency, retry, token, and spend limit independently. | Work stops at the exact bound with no hidden retry or escalation. |
| Crash after budget reservation, after dispatch, and before receipt commit. | Recovery uses the ledger and downstream operation ID; it never blindly repeats a side effect. |
| Remove or fail the audit sink and fill the bounded buffer. | Protected writes stop before unaudited execution. |
| Compromise a specialist to forge approval, receipt, policy version, or success. | Signature and provenance checks reject every forged authority artifact. |
| Fail Toolbox or MCP with timeout, 429, partial response, redirect, and identity change. | Single retry owner respects deadline and idempotency; no privileged fallback or retry storm occurs. |
| Resume a checkpoint after grant expiry, policy revocation, or tool upgrade. | Full execution-time authorization reruns and denies stale authority. |
| Trigger quality escalation to a stronger model. | Escalation creates a distinct attempt and does not inherit or broaden a prior tool grant. |

Property-based tests should generate arbitrary subsets and supersets of allowed arguments to prove monotonic narrowing: adding a permission, resource, destination, data class, use, duration, or cost beyond the grant can never change a denial into an allow. Model-based state-machine tests should prove legal transitions among proposed, denied, pending approval, approved, reserved, dispatched, completed, revoked, cancelled, failed, and outcome unknown.

### Application facade compared with Toolbox and MCP

| Option | Strengths | Limitations for TokenNexus | MVP role |
|---|---|---|---|
| Application-owned capability facade | Direct access to task, attempt, caller, budget, policy, approval, idempotency, and audit state; deterministic and testable; smallest initial external surface. | TokenNexus must implement and operate policy, registry, credential, adapter, and receipt components. | Required primary policy enforcement point. |
| Microsoft Foundry Toolbox | Centralized tool endpoint, managed credentials, authentication and authorization features, guardrails, observability, lifecycle management, and tool versioning. | Toolbox policy is not the TokenNexus task grant; managed defaults or tool versions can change independently; adds service availability and configuration dependencies. | Optional downstream execution and management layer after facade authorization. |
| Direct MCP server | Standard discovery and invocation transport; broad ecosystem; useful adapter boundary. | Authorization is optional in MCP; tool annotations are untrusted; token audience, server identity, schema poisoning, result handling, rate limiting, and logging remain client and server duties. | Optional downstream protocol, restricted to approved pinned servers. |
| Agent Framework middleware only | Natural interception point for model-proposed function calls; can validate, transform, block, or terminate; integrates with workflows and HITL. | Process-local middleware alone is bypassable by alternate clients and does not provide a durable cross-instance grant ledger, credential broker, or organization-wide policy. | Use as an early interception layer that calls the capability facade. |

The facade-versus-Toolbox decision is therefore not exclusive. The MVP should begin with the facade and narrow application adapters. Add Toolbox when multiple agents or applications need centrally managed credentials and tool lifecycle controls. Add MCP when interoperability benefits outweigh the extra protocol and server supply-chain surface. In both cases, pin identities and versions and retain the facade as the final TokenNexus authorization authority.

### Recommended implementation slices

1. Add typed `ToolProposal`, `CapabilityGrant`, `ApprovalRequest`, `ToolExecutionReceipt`, and terminal reason-code contracts to the primary architecture document.
2. Define a versioned policy model for operation impact, resource selectors, data classes, budgets, approval classes, and revocation overlays.
3. Build a deterministic policy service and signed one-use grant issuer with an atomic consume and idempotency ledger.
4. Build the facade with registry resolution, semantic argument validation, approval binding, credential brokering, bounded adapters, result validation, and append-only receipts.
5. Wire Agent Framework function middleware to convert tool calls into proposals and to pause or resume through typed approval requests. Prohibit direct tool registration that bypasses the facade.
6. Implement one low-impact read tool and one approval-required side-effect tool through local adapters before considering Toolbox or MCP.
7. Run the adversarial suite with deterministic substitutes, then add Toolbox or MCP conformance tests for audience binding, identity, schema pinning, timeout, rate limiting, and output sanitization.

### Changes recommended for primary documents

The primary implementation research should make these currently implied requirements explicit:

* Specialists never receive credentials and never invoke protected tools directly.
* Capability grants are per task attempt, signed, short-lived, one-use by default, resource constrained, and checked again at execution.
* Human approval is bound to a canonical call digest and cannot authorize changed arguments.
* Tool identity includes implementation and schema digests; annotations and descriptions are untrusted.
* Revocation distinguishes pre-dispatch prevention from in-flight cancellation and reconciliation.
* Unknown side-effect outcome is a first-class terminal state that blocks dependent operations.
* Raw prompts, tokens, secrets, and unrestricted tool payloads are excluded from audit by default.
* Foundry Toolbox and MCP are downstream transports or management layers, never substitutes for the TokenNexus grant evaluator.

The PRD should add acceptance criteria for grant replay prevention, approval mutation, revocation timing, audit sequence completeness, unsafe tool output, compromised specialist behavior, and fail-closed behavior when policy, registry, credential, approval, or audit dependencies are unavailable.

### Residual risks

* A malicious but correctly authorized user can still cause permitted harm; impact policy, quotas, anomaly detection, and separation of duties reduce but do not eliminate insider risk.
* A downstream system may perform an irreversible action before a timeout or revocation reaches it. Idempotency, operation IDs, reconciliation, and explicit unknown outcomes contain this risk.
* Semantic classification of tool purpose and impact can be wrong. Keep classification in reviewed registry data, require approval for unknown impact, and test tool updates before activation.
* A compromised facade, policy service, registry, credential broker, or audit signing key defeats central controls. Isolate these components, use managed identities and hardware-backed keys, separate administration, rotate keys, and monitor configuration integrity.
* Human approval does not guarantee informed judgment. Clear disclosure, role checks, dual control, and anti-fatigue design are necessary but imperfect.
* Result validation cannot prove semantic truth. Provenance, independent quality evaluation, deterministic checks, and restrained downstream use remain necessary.
* Toolbox, MCP, Agent Framework, model, and provider behavior will evolve. Pin versions where possible and continuously rerun conformance and adversarial tests.

## References

### Local evidence

* docs/prds/tokennexus-ai-framework-prd.md: product principles, bounded agent and tool path, deny-by-default tools, budgets, execution records, adversarial testing, data minimization, and degradation requirements.
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md: deterministic control plane, typed specialist contracts, explicit run state, capability facade, journal, and validation invariants.
* .copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md: coordinator authority, per-attempt grants, correlation, idempotency, deadlines, cancellation, protected tools, and deterministic handoff tests.
* .copilot-tracking/research/subagents/2026-09-15/conversation-memory-research.md: ephemeral memory recommendation, isolation and retention controls, and the rule that retrieved memory cannot change identity, policy, budget, or grants.
* docs/brds/tokennexus-ai-framework-brd.md: business objectives for cost control, governance, auditability, security, and policy enforcement.

### External evidence

* [Microsoft Agent Framework tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/) describes agent function tools and their invocation surface.
* [Microsoft Agent Framework middleware](https://learn.microsoft.com/en-us/agent-framework/agents/middleware) documents function middleware interception, validation, transformation, blocking, and termination behavior.
* [Microsoft Agent Framework workflows](https://learn.microsoft.com/en-us/agent-framework/concepts/workflows/) describes explicit graph-based orchestration and typed executors.
* [Microsoft Agent Framework human-in-the-loop](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) documents typed approval requests and resume semantics.
* [Microsoft Agent Framework checkpoints](https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints) documents workflow restoration, including pending requests.
* [Microsoft Agent Framework handoff orchestration](https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/handoff) documents decentralized ownership transfer, which is unsuitable as the TokenNexus policy authority.
* [Microsoft Foundry Toolbox overview](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/toolbox-overview) describes the managed MCP-compatible endpoint, centralized credentials, guardrails, observability, and tool lifecycle or versioning capabilities.
* [MCP authorization specification](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) requires resource or audience binding where authorization is implemented and prohibits token passthrough.
* [MCP tools specification](https://modelcontextprotocol.io/specification/2025-06-18/server/tools) states that tool annotations are untrusted and assigns validation, confirmation, access control, timeout, rate-limit, sanitization, and logging responsibilities to implementations.
* [OWASP LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) supports treating direct and indirect content as untrusted and separating authority from model interpretation.
* [OWASP LLM02: Sensitive Information Disclosure](https://genai.owasp.org/llmrisk/llm02-sensitive-information-disclosure/) supports data minimization, access control, and output filtering.
* [OWASP LLM05: Improper Output Handling](https://genai.owasp.org/llmrisk/llm05-improper-output-handling/) supports treating model and tool output as untrusted before downstream use.
* [OWASP LLM06: Excessive Agency](https://genai.owasp.org/llmrisk/llm06-excessive-agency/) supports minimizing tools, permissions, autonomy, and side effects and requiring human approval for high-impact actions.
* [OWASP LLM10: Unbounded Consumption](https://genai.owasp.org/llmrisk/llm10-unbounded-consumption/) supports rate limits, quotas, timeouts, input limits, and resource monitoring.
* [RFC 8707: Resource Indicators for OAuth 2.0](https://www.rfc-editor.org/rfc/rfc8707.html) defines audience-bound access token requests used to prevent confused-deputy token reuse.
* [OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html) provides current token, redirect, sender, and authorization security guidance.
