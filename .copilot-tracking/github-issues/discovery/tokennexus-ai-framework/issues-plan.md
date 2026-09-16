<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Issues Plan

* **Repository**: TokenNexus-AI/TokenNexus-AI (provisional)
* **Milestone**: MVP Sprint for P0 stories; none for deferred stories
* **Execution State**: Review only. Similarity search and every GitHub mutation remain pending.

## IS001 - Create - Governed request orchestration epic

Create the parent for contracts, deterministic coordination, and model boundaries.

* IS001 - issue_number: {{TEMP-1}}
* IS001 - title: feat(core): establish governed request orchestration
* IS001 - state: open
* IS001 - labels: Epic, P0-must-have, general-agent
* IS001 - milestone: MVP Sprint
* IS001 - assignees: none

### IS001 - body

```markdown
## Outcome

Establish an application-owned control plane that accepts versioned requests and deterministically owns routing, budget, authorization, quality, escalation, idempotency, and terminal outcomes.

## Acceptance Criteria

### Bounded orchestration

* Given the epic's P0 user stories are complete, when valid, invalid, replayed, cancelled, and timed-out requests execute, then each request reaches one replay-safe terminal outcome without duplicate paid work.
* Given specialist or model output proposes a state transition, when the coordinator evaluates it, then deterministic policy remains the only authority for the transition.

## Source

Product requirements: FR-001, FR-007, FR-012, NFR-007, NFR-008, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS001 - Relationships

* IS001 - parent-of - {{TEMP-9}}: Versioned API contracts
* IS001 - parent-of - {{TEMP-10}}: Deterministic coordinator and journal
* IS001 - parent-of - {{TEMP-11}}: Provider-neutral model adapters

## IS002 - Create - Economics policy epic

Create the parent for routing, cost estimation, budget control, and policy administration.

* IS002 - issue_number: {{TEMP-2}}
* IS002 - title: feat(economics): govern routing and request budgets
* IS002 - state: open
* IS002 - labels: Epic, P0-must-have, billing-agent
* IS002 - milestone: MVP Sprint
* IS002 - assignees: none

### IS002 - body

```markdown
## Outcome

Choose the lowest-cost eligible execution path expected to satisfy declared quality, latency, budget, and governance constraints.

## Acceptance Criteria

### Governed economics

* Given approved policy, pricing, and model aliases, when a request is admitted, then only an eligible and sufficiently funded path can start.
* Given a routing or budget decision, when the result is recorded, then it includes the policy version, estimate, action, and stable public reason codes.

## Source

Product requirements: FR-002, FR-003, FR-011, G-001, and G-003 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS002 - Relationships

* IS002 - parent-of - {{TEMP-12}}: Versioned model routing
* IS002 - parent-of - {{TEMP-13}}: Cost estimation and budget actions
* IS002 - parent-of - {{TEMP-14}}: Policy administration

## IS003 - Create - Quality and semantic reuse epic

Create the parent for semantic cache, quality evaluation, one-step escalation, and degraded outcomes.

* IS003 - issue_number: {{TEMP-3}}
* IS003 - title: feat(quality): control cache, evaluation, and escalation
* IS003 - state: open
* IS003 - labels: Epic, P0-must-have, technical-agent
* IS003 - milestone: MVP Sprint
* IS003 - assignees: none

### IS003 - body

```markdown
## Outcome

Reuse only safe equivalent results, score every model response, and escalate insufficient quality no more than once under the same request controls.

## Acceptance Criteria

### Quality control

* Given cacheable, non-cacheable, passing, failing, and evaluator-unavailable cases, when the quality pipeline runs, then each case produces the expected bounded action and evidence.
* Given a low-quality attempt, when escalation is allowed or forbidden, then one linked retry runs or a controlled quality-unmet result identifies the public reason.

## Source

Product requirements: FR-005 through FR-008, FR-013, NFR-002, NFR-004, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS003 - Relationships

* IS003 - parent-of - {{TEMP-15}}: Scoped semantic cache
* IS003 - parent-of - {{TEMP-16}}: Quality evaluator
* IS003 - parent-of - {{TEMP-17}}: One-step escalation
* IS003 - parent-of - {{TEMP-18}}: Controlled degraded outcomes

## IS004 - Create - Protected specialist and tool epic

Create the parent for authorization, capability mediation, and content protection.

* IS004 - issue_number: {{TEMP-4}}
* IS004 - title: feat(security): enforce protected specialist and tool actions
* IS004 - state: open
* IS004 - labels: Epic, P0-must-have, technical-agent
* IS004 - milestone: MVP Sprint
* IS004 - assignees: none

### IS004 - body

```markdown
## Outcome

Keep specialists and untrusted content from obtaining authority, reusable credentials, unconstrained tools, or sensitive retained data.

## Acceptance Criteria

### Complete mediation

* Given unauthorized actors, injected instructions, argument smuggling, replay, and unknown tool outcomes, when protected actions are proposed, then the server denies or safely reconciles them before further side effects.
* Given an authorized bounded call, when the capability facade dispatches it, then authorization, exact approval, budget reservation, one-use grant consumption, and a durable receipt are present.

## Source

Product requirements: FR-014, FR-016, FR-020, NFR-001, NFR-002, NFR-010, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS004 - Relationships

* IS004 - parent-of - {{TEMP-19}}: Protected-action roles
* IS004 - parent-of - {{TEMP-20}}: Capability facade
* IS004 - parent-of - {{TEMP-21}}: Secret and content minimization

## IS005 - Create - Client and session epic

Create the parent for the usable request workspace, recovery behavior, explanations, and feedback.

* IS005 - issue_number: {{TEMP-5}}
* IS005 - title: feat(client): deliver the request workspace and recoverable sessions
* IS005 - state: open
* IS005 - labels: Epic, P0-must-have, general-agent
* IS005 - milestone: MVP Sprint
* IS005 - assignees: none

### IS005 - body

```markdown
## Outcome

Provide a usable first-screen request experience that explains governed outcomes and preserves non-sensitive work across authorization interruptions.

## Acceptance Criteria

### User journeys

* Given routine, complex, cached, escalated, over-budget, and denied journeys, when a user completes each flow, then the client presents the response or controlled status with one safe next action.
* Given a valid session, when the user continues work, then authentication is reused and only structured non-sensitive recovery state persists.

## Source

Product requirements: Product Overview, FR-015, FR-017, FR-019, NFR-003, NFR-009, and NFR-011 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS005 - Relationships

* IS005 - parent-of - {{TEMP-22}}: Request workspace
* IS005 - parent-of - {{TEMP-23}}: Session recovery
* IS005 - parent-of - {{TEMP-24}}: Decision summary
* IS005 - parent-of - {{TEMP-25}}: User feedback

## IS006 - Create - Observability and evidence epic

Create the parent for durable execution records, OpenTelemetry, economics reporting, and compliance evidence.

* IS006 - issue_number: {{TEMP-6}}
* IS006 - title: feat(evidence): provide economics observability and control evidence
* IS006 - state: open
* IS006 - labels: Epic, P0-must-have, observability
* IS006 - milestone: MVP Sprint
* IS006 - assignees: none

### IS006 - body

```markdown
## Outcome

Make every material decision observable while keeping authoritative economics and security evidence independent of sampled telemetry.

## Acceptance Criteria

### Complete and safe evidence

* Given completed evaluation requests and protected actions, when evidence is inspected, then required execution, trace, audit, and control fields are complete and correlated.
* Given telemetry sampling or exporter failure, when evidence is queried, then durable execution and security records remain complete without raw prompts, responses, or credentials.

## Source

Product requirements: FR-009, FR-010, FR-018, G-005, G-007, and CR-001 through CR-008 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS006 - Relationships

* IS006 - parent-of - {{TEMP-26}}: Execution journal
* IS006 - parent-of - {{TEMP-27}}: OpenTelemetry export
* IS006 - parent-of - {{TEMP-28}}: Baseline reporting
* IS006 - parent-of - {{TEMP-29}}: Compliance evidence catalog

## IS007 - Create - Azure runtime epic

Create the parent for Azure hosting, Foundry deployments, managed identity, and operational rollback.

* IS007 - issue_number: {{TEMP-7}}
* IS007 - title: feat(platform): deploy the Azure MVP runtime
* IS007 - state: open
* IS007 - labels: Epic, P0-must-have, infrastructure
* IS007 - milestone: MVP Sprint
* IS007 - assignees: none

### IS007 - body

```markdown
## Outcome

Deploy the stateless control-plane API independently from two alias-resolved model deployments using reproducible environment configuration and least-privilege identity.

## Acceptance Criteria

### Reproducible runtime

* Given an approved Azure subscription, region, and model pair, when the environment deploys, then the API runs on Azure Container Apps and reaches both Microsoft Foundry model aliases through managed identity.
* Given a failed revision or model replacement, when rollback runs, then the last approved configuration and alias mapping are restored with recorded evidence.

## Source

Product requirements: Dependencies, Operational Considerations, and Rollout and Release Plan in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS007 - Relationships

* IS007 - parent-of - {{TEMP-30}}: Container Apps and Foundry deployment
* IS007 - parent-of - {{TEMP-31}}: Managed identity and versioned settings
* IS007 - parent-of - {{TEMP-32}}: Rollback and capacity validation

## IS008 - Create - MVP validation epic

Create the parent for deterministic testing, end-to-end acceptance, and release quality gates.

* IS008 - issue_number: {{TEMP-8}}
* IS008 - title: test(mvp): prove release acceptance and quality gates
* IS008 - state: open
* IS008 - labels: Epic, P0-must-have, general-agent
* IS008 - milestone: MVP Sprint
* IS008 - assignees: none

### IS008 - body

```markdown
## Outcome

Produce reproducible evidence that the MVP satisfies every Must requirement, all seven goals, and all eight required acceptance scenarios.

## Acceptance Criteria

### Release decision

* Given a frozen evaluation manifest and deterministic substitutes, when the acceptance suite runs twice, then policy outcomes and exact call counts remain stable.
* Given all P0 stories are complete, when the release gate runs, then every Must requirement, goal, acceptance scenario, and applicable control has passing evidence or the release is blocked.

## Source

Product requirements: MVP Exit Rule, Required Acceptance Scenarios, and Approval Criteria in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS008 - Relationships

* IS008 - parent-of - {{TEMP-33}}: Deterministic test harness
* IS008 - parent-of - {{TEMP-34}}: Eight acceptance scenarios
* IS008 - parent-of - {{TEMP-35}}: Performance, accessibility, and release checks

## IS009 - Create - Versioned API contracts story

* IS009 - issue_number: {{TEMP-9}}
* IS009 - title: feat(api): publish versioned request and result contracts
* IS009 - state: open
* IS009 - labels: User Story, P0-must-have, P0, general-agent
* IS009 - milestone: MVP Sprint
* IS009 - assignees: none

### IS009 - body

```markdown
## User Story

As an AI application developer, I want stable provider-neutral request and result contracts so that I can integrate once and receive actionable validation errors and governed outcomes.

## Acceptance Criteria

### Valid request

* Given a request with valid task, criticality, quality, latency, budget, cache, and sensitivity fields, when it is admitted, then values are normalized and a UUIDv7 request ID is assigned.

### Invalid request

* Given an unknown property or invalid constraint, when validation runs, then execution does not start and an RFC 9457 response identifies the field and safe corrective action.

### Compatibility

* Given published Draft 2020-12 schemas and a closed dotted reason-code registry, when contract fixtures are validated across supported runtimes, then canonical decimals, RFC 3339 timestamps, and semantic versions produce identical results.

## Source

FR-001, FR-019, and NFR-003 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS009 - Relationships

* IS009 - sub-issue-of - {{TEMP-1}}: Governed request orchestration

## IS010 - Create - Deterministic coordinator story

* IS010 - issue_number: {{TEMP-10}}
* IS010 - title: feat(core): implement deterministic coordinator and idempotency journal
* IS010 - state: open
* IS010 - labels: User Story, P0-must-have, P0, general-agent
* IS010 - milestone: MVP Sprint
* IS010 - assignees: none

### IS010 - body

```markdown
## User Story

As a platform operator, I want one deterministic coordinator to own every governed transition so that retries, replays, cancellation, and escalation cannot create uncontrolled work.

## Acceptance Criteria

### Replay safety

* Given the same scoped idempotency key and RFC 8785 request fingerprint, when a request is replayed, then the in-progress status or stored terminal result returns without duplicate paid or side-effecting work.
* Given the same key with a different fingerprint, when admission runs, then it returns `request.idempotency_conflict` before execution.

### Resource bounds

* Given cancellation, deadline expiry, or a terminal state, when a late or retried result arrives, then it cannot start new work or mutate the terminal result.
* Given a low-quality first attempt, when the run proceeds, then there are at most two quality attempts, one escalation, one centralized transient retry allowance, and reserved budget before each paid operation.

## Source

FR-007, NFR-007, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS010 - Relationships

* IS010 - sub-issue-of - {{TEMP-1}}: Governed request orchestration

## IS011 - Create - Model adapters story

* IS011 - issue_number: {{TEMP-11}}
* IS011 - title: feat(models): add provider-neutral model adapters and deterministic substitutes
* IS011 - state: open
* IS011 - labels: User Story, P0-must-have, P0, technical-agent
* IS011 - milestone: MVP Sprint
* IS011 - assignees: none

### IS011 - body

```markdown
## User Story

As an AI application developer, I want economical and capable model aliases behind one interface so that providers and deterministic test substitutes can change without changing my contract.

## Acceptance Criteria

### Adapter parity

* Given either physical model deployment, when the common adapter is invoked, then it returns the same specialist result shape with usage, latency, cost, status, and safe reason codes.
* Given deterministic model substitutes, when policy tests repeat, then configured outputs and exact call counts remain stable without Azure dependencies.

### Retry ownership

* Given provider SDK retry behavior, when adapters initialize, then hidden retries are disabled or surfaced to the coordinator's single request-level retry allowance.

## Source

FR-012, NFR-007, and NFR-008 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS011 - Relationships

* IS011 - sub-issue-of - {{TEMP-1}}: Governed request orchestration

## IS012 - Create - Policy routing story

* IS012 - issue_number: {{TEMP-12}}
* IS012 - title: feat(routing): select eligible models with versioned policy
* IS012 - state: open
* IS012 - labels: User Story, P0-must-have, P0, billing-agent
* IS012 - milestone: MVP Sprint
* IS012 - assignees: none

### IS012 - body

```markdown
## User Story

As a platform operator, I want deterministic policy to choose an eligible model alias so that routine work uses an economical path and critical work receives sufficient capability.

## Acceptance Criteria

### Route selection

* Given at least 30 labeled requests including routine, complex, and critical cases, when routing runs under a frozen policy, then at least 90% match expected aliases.
* Given each routing decision, when its evidence is recorded, then it includes model alias, policy version, estimate, eligibility gates, and stable public reason codes.

### Policy authority

* Given a model or specialist recommends a different route, when the coordinator evaluates the recommendation, then it cannot override deterministic policy, budget, quality, latency, or authorization gates.

## Source

FR-002 and G-001 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS012 - Relationships

* IS012 - sub-issue-of - {{TEMP-2}}: Economics policy

## IS013 - Create - Budget enforcement story

* IS013 - issue_number: {{TEMP-13}}
* IS013 - title: feat(budget): estimate cost and enforce request budget actions
* IS013 - state: open
* IS013 - labels: User Story, P0-must-have, P0, billing-agent
* IS013 - milestone: MVP Sprint
* IS013 - assignees: none

### IS013 - body

```markdown
## User Story

As a FinOps analyst, I want cost estimated and governed before execution so that no request reaches a disallowed paid path.

## Acceptance Criteria

### Budget action

* Given at least five over-budget requests, when admission evaluates fixed versioned pricing, then none starts a disallowed paid operation and each returns downgrade, approval-required, or block.
* Given downgrade is considered, when the lower-cost path cannot still satisfy quality and policy gates, then the request requires approval or is blocked.

### Reservation

* Given any paid attempt or protected tool call, when dispatch begins, then sufficient cost, token, time, and tool allowances have been atomically reserved and recorded.

## Source

FR-003, G-003, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS013 - Relationships

* IS013 - sub-issue-of - {{TEMP-2}}: Economics policy

## IS014 - Create - Policy administration story

* IS014 - issue_number: {{TEMP-14}}
* IS014 - title: feat(policy): administer confirmed versioned policy changes
* IS014 - state: open
* IS014 - labels: User Story, P0-must-have, P0, billing-agent
* IS014 - milestone: MVP Sprint
* IS014 - assignees: none

### IS014 - body

```markdown
## User Story

As an authorized platform operator, I want to update versioned routing policy without an application deployment so that approved economics controls can evolve safely.

## Acceptance Criteria

### Confirmed update

* Given an authorized operator and a valid proposed change, when the operator confirms it, then a new immutable policy version and audit event are created and subsequent requests use the new version.
* Given an unauthorized, unconfirmed, or invalid change, when administration is attempted, then the server denies it and the active policy remains unchanged.

### Rollback

* Given a prior approved policy version, when rollback is confirmed, then subsequent requests use that policy through a new auditable version transition.

## Source

FR-011 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS014 - Relationships

* IS014 - sub-issue-of - {{TEMP-2}}: Economics policy

## IS015 - Create - Semantic cache story

* IS015 - issue_number: {{TEMP-15}}
* IS015 - title: feat(cache): implement scoped semantic response reuse
* IS015 - state: open
* IS015 - labels: User Story, P0-must-have, P0, technical-agent
* IS015 - milestone: MVP Sprint
* IS015 - assignees: none

### IS015 - body

```markdown
## User Story

As an end user, I want eligible equivalent requests to reuse approved results so that routine responses are faster and avoid model cost without crossing privacy or freshness boundaries.

## Acceptance Criteria

### Eligible reuse

* Given at least ten approved paraphrases across five source answers, when lookup uses the frozen embedding version and pilot threshold, then at least 80% hit and valid hits make no model call.

### Mandatory bypass

* Given stale, sensitive, personalized, freshness-critical, tool-bearing, degraded, non-final, or cross-scope content, when lookup and storage are evaluated, then the cache is bypassed with a stable reason code.
* Given tenant, application, use case, policy, model, embedding, authorization cohort, locale, or freshness differs, when lookup runs, then no entry from the other scope is returned.

## Source

FR-005, NFR-002, and G-004 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS015 - Relationships

* IS015 - sub-issue-of - {{TEMP-3}}: Quality and semantic reuse

## IS016 - Create - Quality evaluator story

* IS016 - issue_number: {{TEMP-16}}
* IS016 - title: feat(quality): evaluate every non-cached response
* IS016 - state: open
* IS016 - labels: User Story, P0-must-have, P0, technical-agent
* IS016 - milestone: MVP Sprint
* IS016 - assignees: none

### IS016 - body

```markdown
## User Story

As a governance operator, I want every model response evaluated with deterministic checks and a versioned rubric so that quality decisions are reviewable and cannot authorize unsafe work.

## Acceptance Criteria

### Evaluation evidence

* Given a non-cached response, when evaluation completes, then the record includes hard-check results, 1-5 score, threshold, pass state, evaluator and rubric versions, attempt ID, latency, usage, and cost.
* Given a deterministic safety, schema, citation, or policy check fails, when the judge score is high, then the failed hard check still prevents a passing result.

### Unavailable evaluator

* Given the judge is unavailable or malformed after the bounded transient retry, when routine output is otherwise valid, then quality is unknown, the result is degraded, and no quality escalation is inferred from the outage.

## Source

FR-006 and G-003 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS016 - Relationships

* IS016 - sub-issue-of - {{TEMP-3}}: Quality and semantic reuse

## IS017 - Create - One-step escalation story

* IS017 - issue_number: {{TEMP-17}}
* IS017 - title: feat(escalation): retry low-quality output once when eligible
* IS017 - state: open
* IS017 - labels: User Story, P0-must-have, P0, technical-agent
* IS017 - milestone: MVP Sprint
* IS017 - assignees: none

### IS017 - body

```markdown
## User Story

As an end user, I want a low-quality economical response retried once on a capable model when allowed so that quality improves without unbounded spend.

## Acceptance Criteria

### Eligible escalation

* Given a first attempt below threshold with sufficient policy, budget, and deadline allowance, when escalation is evaluated, then one capable-model attempt runs under the same request ID with a distinct linked attempt ID.

### Controlled non-escalation

* Given policy, budget, or latency forbids escalation, when the first attempt is below threshold, then no second attempt starts and the result reports quality unmet with the allowed public reason.
* Given the second attempt remains below threshold, when final evaluation completes, then no third attempt starts and the controlled terminal result links both attempts.

## Source

FR-007, FR-008, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS017 - Relationships

* IS017 - sub-issue-of - {{TEMP-3}}: Quality and semantic reuse

## IS018 - Create - Controlled degradation story

* IS018 - issue_number: {{TEMP-18}}
* IS018 - title: feat(runtime): return controlled degraded outcomes
* IS018 - state: open
* IS018 - labels: User Story, P1-should-have, technical-agent
* IS018 - milestone: none
* IS018 - assignees: none

### IS018 - body

```markdown
## User Story

As an end user, I want optional dependency failures to produce truthful bounded outcomes so that routine work can continue without hiding uncertainty.

## Acceptance Criteria

### Safe degradation

* Given evaluator, cache, or telemetry enrichment is unavailable and routine inference can continue safely, when the request completes, then the result is marked degraded with component status and no secret or internal diagnostic.
* Given identity, authorization, required audit evidence, or protected-tool policy is unavailable, when a protected action is attempted, then it fails closed rather than degrading to a more privileged path.

### Bounded dependencies

* Given provider or dependency timeout, when the absolute request deadline expires, then in-flight work is cancelled where supported and no fallback exceeds the original allowances.

## Source

FR-013 and NFR-004 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS018 - Relationships

* IS018 - sub-issue-of - {{TEMP-3}}: Quality and semantic reuse

## IS019 - Create - Protected-action authorization story

* IS019 - issue_number: {{TEMP-19}}
* IS019 - title: feat(auth): enforce server-side roles for protected actions
* IS019 - state: open
* IS019 - labels: User Story, P0-must-have, P0, technical-agent
* IS019 - milestone: MVP Sprint
* IS019 - assignees: none

### IS019 - body

```markdown
## User Story

As a security operator, I want protected actions enforced by server-side role checks so that hidden client controls cannot be bypassed.

## Acceptance Criteria

### Deny by default

* Given at least ten unauthorized policy, export, and cache-action tests including direct API calls, when each action is attempted, then all are denied and audited without changing protected state.
* Given required identity, role, tenant, audience, or policy evidence is missing, when authorization runs, then it denies before credentials or sensitive data are released.

### Authorized action

* Given an actor with the required role and scope, when a valid protected action is requested, then the action passes server-side authorization and its audit record identifies actor, action, policy version, and decision.

## Source

FR-016 and NFR-010 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS019 - Relationships

* IS019 - sub-issue-of - {{TEMP-4}}: Protected specialist and tool actions

## IS020 - Create - Capability facade story

* IS020 - issue_number: {{TEMP-20}}
* IS020 - title: feat(tools): mediate bounded specialist tool calls
* IS020 - state: open
* IS020 - labels: User Story, P0-must-have, P0, technical-agent
* IS020 - milestone: MVP Sprint
* IS020 - assignees: none

### IS020 - body

```markdown
## User Story

As a security operator, I want every specialist tool proposal mediated by an application-owned capability facade so that model output can propose work but never grant authority.

## Acceptance Criteria

### Complete mediation

* Given a typed proposal and one-use attempt-bound grant, when a tool call is requested, then the facade validates trusted identity, task state, pinned tool and schema digests, canonical arguments, resource scope, current entitlement, revocation, budget, and exact approval before dispatch.
* Given arguments, tool identity, approval digest, audience, or resource scope differ from the grant, when validation runs, then the call is denied before credential minting.

### Side-effect safety

* Given an authorized call, when dispatch begins, then grant consumption, budget reservation, and idempotency claim are atomic and the downstream credential is short-lived, least-privilege, and audience-bound.
* Given a side-effect acknowledgement is unknown, when the adapter returns, then the run fails with `tool.outcome_unknown`, replay and dependent operations are blocked, and reconciliation evidence is retained.

## Source

FR-020, CR-006, CR-007, and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS020 - Relationships

* IS020 - sub-issue-of - {{TEMP-4}}: Protected specialist and tool actions

## IS021 - Create - Secret and content minimization story

* IS021 - issue_number: {{TEMP-21}}
* IS021 - title: feat(privacy): externalize secrets and minimize retained content
* IS021 - state: open
* IS021 - labels: User Story, P0-must-have, P0, technical-agent
* IS021 - milestone: MVP Sprint
* IS021 - assignees: none

### IS021 - body

```markdown
## User Story

As a governance operator, I want secrets externalized and raw AI content excluded from storage by default so that economics evidence does not create unnecessary disclosure risk.

## Acceptance Criteria

### Secret protection

* Given repository source, configuration, logs, traces, errors, checkpoints, cache records, and UI details, when secret and canary scans run, then no credentials or seeded secrets are present.

### Data minimization

* Given default production configuration, when requests execute, then provider conversation storage and raw prompt, response, hidden-instruction, and tool-payload persistence are disabled.
* Given approved diagnostic capture is enabled, when content crosses a storage or telemetry boundary, then allowlist filtering, redaction, access control, retention, and deletion evidence apply.

## Source

FR-014, NFR-001, NFR-002, CR-004, and CR-006 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS021 - Relationships

* IS021 - sub-issue-of - {{TEMP-4}}: Protected specialist and tool actions

## IS022 - Create - Request workspace story

* IS022 - issue_number: {{TEMP-22}}
* IS022 - title: feat(client): build the usable request workspace
* IS022 - state: open
* IS022 - labels: User Story, P0-must-have, P0, general-agent
* IS022 - milestone: MVP Sprint
* IS022 - assignees: none

### IS022 - body

```markdown
## User Story

As an end user, I want the first screen to be a usable request workspace so that I can submit work, set constraints, inspect the response, and recover from controlled errors.

## Acceptance Criteria

### Primary workspace

* Given an authenticated user opens the client, when the first screen renders, then it provides task input, optional business constraints, execution action, response area, concise decision details, feedback entry point, and error state.
* Given a request is in progress, complete, blocked, degraded, or quality-unmet, when state changes, then controls and status remain coherent without losing non-sensitive input.

### Protected controls

* Given routine and administrative actions, when the workspace renders, then protected policy and export actions are visibly separated while server-side authorization remains authoritative.

## Source

Reference Client Experience and Primary User Journeys in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS022 - Relationships

* IS022 - sub-issue-of - {{TEMP-5}}: Client and recoverable sessions

## IS023 - Create - Session recovery story

* IS023 - issue_number: {{TEMP-23}}
* IS023 - title: feat(session): preserve non-sensitive work across interruptions
* IS023 - state: open
* IS023 - labels: User Story, P0-must-have, P0, general-agent
* IS023 - milestone: MVP Sprint
* IS023 - assignees: none

### IS023 - body

```markdown
## User Story

As an end user, I want valid sessions reused and non-sensitive work preserved after a denial so that security controls do not force unnecessary rework.

## Acceptance Criteria

### Session reuse

* Given ten scripted journeys within a valid session, when users continue work, then at least nine avoid repeated authentication.
* Given the pilot inactivity or absolute TTL expires, when the next action occurs, then reauthentication is required without restoring expired sensitive content.

### Recovery state

* Given a protected action is denied, when the response returns, then non-sensitive input remains and exactly one permitted recovery action is presented.
* Given concurrent session updates, when ETag compare-and-swap detects a conflict, then the service deterministically merges commutative metadata or returns a retryable conflict instead of losing constraints.

## Source

FR-017 and NFR-011 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS023 - Relationships

* IS023 - sub-issue-of - {{TEMP-5}}: Client and recoverable sessions

## IS024 - Create - Decision summary story

* IS024 - issue_number: {{TEMP-24}}
* IS024 - title: feat(explainability): present safe decision summaries
* IS024 - state: open
* IS024 - labels: User Story, P0-must-have, P0, general-agent
* IS024 - milestone: MVP Sprint
* IS024 - assignees: none

### IS024 - body

```markdown
## User Story

As an end user, I want a concise explanation of each outcome so that I understand model, economics, quality, cache, and escalation decisions without seeing sensitive internals.

## Acceptance Criteria

### Complete summary

* Given completed, cached, escalated, blocked, degraded, and quality-unmet outcomes, when the result is returned, then the summary includes model alias, estimated cost, latency, quality state, cache state, escalation state, and allowlisted public reason codes.

### Safe transparency

* Given hidden prompts, provider deployment details, credentials, internal diagnostics, or sensitive content exist, when the summary is generated and rendered, then none is exposed.

## Source

FR-019, NFR-003, and CR-008 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS024 - Relationships

* IS024 - sub-issue-of - {{TEMP-5}}: Client and recoverable sessions

## IS025 - Create - User feedback story

* IS025 - issue_number: {{TEMP-25}}
* IS025 - title: feat(feedback): record explicit user ratings
* IS025 - state: open
* IS025 - labels: User Story, P2-future, general-agent
* IS025 - milestone: none
* IS025 - assignees: none

### IS025 - body

```markdown
## User Story

As an end user, I want to rate a completed outcome so that the product team can evaluate future policy improvements without automatic learning.

## Acceptance Criteria

### Feedback record

* Given a completed request, when a user submits a valid rating and optional category, then the feedback is linked to the request ID and an event is recorded.
* Given feedback is submitted, when subsequent requests route, then no policy, threshold, or model alias changes automatically.

## Source

FR-015 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS025 - Relationships

* IS025 - sub-issue-of - {{TEMP-5}}: Client and recoverable sessions

## IS026 - Create - Execution record story

* IS026 - issue_number: {{TEMP-26}}
* IS026 - title: feat(journal): persist immutable execution economics records
* IS026 - state: open
* IS026 - labels: User Story, P0-must-have, P0, observability
* IS026 - milestone: MVP Sprint
* IS026 - assignees: none

### IS026 - body

```markdown
## User Story

As a FinOps analyst, I want an immutable terminal execution record so that cost, quality, and control outcomes can be reproduced independently of telemetry sampling.

## Acceptance Criteria

### Record completeness

* Given every completed evaluation request, when the execution record is projected, then required request, policy, alias, reason, token, cost, latency, quality, cache, escalation, tool, and status fields pass the versioned schema.
* Given raw prompt or response content, when the record is persisted, then only approved metadata and redacted fields are retained.

### Terminal immutability

* Given a terminal execution record, when a late attempt or exporter retry occurs, then the record cannot be mutated and any additional operational evidence is separately linked.

## Source

FR-009 and G-005 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS026 - Relationships

* IS026 - sub-issue-of - {{TEMP-6}}: Observability and evidence

## IS027 - Create - OpenTelemetry story

* IS027 - issue_number: {{TEMP-27}}
* IS027 - title: feat(telemetry): export metadata-only OpenTelemetry traces and metrics
* IS027 - state: open
* IS027 - labels: User Story, P0-must-have, P0, observability
* IS027 - milestone: MVP Sprint
* IS027 - assignees: none

### IS027 - body

```markdown
## User Story

As a platform operator, I want correlated metadata-only traces and low-cardinality metrics so that I can diagnose model, policy, cache, quality, escalation, and tool behavior safely.

## Acceptance Criteria

### Trace shape

* Given an accepted request, when it executes, then one W3C trace correlates the HTTP server, product request, policy, cache, model, quality, escalation, authorization, and tool spans using standard GenAI and versioned `tokennexus.*` attributes.
* Given queued, resumed, retried, or escalated work, when causality is not strict nesting, then span links preserve the relationship.

### Privacy and metrics

* Given production defaults, when telemetry exports to Application Insights, then raw AI content is absent and baggage is cleared at third-party, public outbound, and cross-tenant boundaries.
* Given metrics are emitted, when dimensions are inspected, then request, trace, attempt, user, tenant, session, cache key, URL, and exception message are not dimensions.

## Source

G-005, NFR-001, and NFR-003 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS027 - Relationships

* IS027 - sub-issue-of - {{TEMP-6}}: Observability and evidence

## IS028 - Create - Baseline reporting story

* IS028 - issue_number: {{TEMP-28}}
* IS028 - title: feat(reporting): compare MVP economics with the all-frontier baseline
* IS028 - state: open
* IS028 - labels: User Story, P0-must-have, P0, observability, billing-agent
* IS028 - milestone: MVP Sprint
* IS028 - assignees: none

### IS028 - body

```markdown
## User Story

As an executive sponsor, I want TokenNexus compared with an all-frontier baseline under identical assumptions so that savings and quality claims are reproducible.

## Acceptance Criteria

### Paired comparison

* Given at least 30 frozen requests, prices, model versions, evaluator version, and environment, when TokenNexus and all-frontier runs complete, then the report pairs routing, tokens, estimated cost, latency, quality, cache, and escalation for every request.
* Given the paired results, when goal metrics are calculated, then mean estimated cost is at least 20% lower with no more than 5% relative quality degradation or the goal is reported as unmet.

### Assumptions

* Given a report viewer, when assumptions are inspected, then model aliases, physical versions, price manifest, evaluation manifest, and known estimate limitations are visible.

## Source

FR-010 and G-002 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS028 - Relationships

* IS028 - sub-issue-of - {{TEMP-6}}: Observability and evidence

## IS029 - Create - Compliance evidence story

* IS029 - issue_number: {{TEMP-29}}
* IS029 - title: feat(compliance): assemble the MVP evidence catalog
* IS029 - state: open
* IS029 - labels: User Story, P0-must-have, P0, observability
* IS029 - milestone: MVP Sprint
* IS029 - assignees: none

### IS029 - body

```markdown
## User Story

As a governance operator, I want a catalog of evidence for every applicable MVP control so that intended use, measurement, oversight, privacy, access, tool safety, consumption bounds, and transparency are reviewable.

## Acceptance Criteria

### Control coverage

* Given controls CR-001 through CR-008, when the evidence catalog is generated, then each control links its named versioned artifact or an approved non-applicable rationale with owner and review status.
* Given a required artifact is absent, stale, or fails validation, when release readiness is evaluated, then the control remains incomplete and the release gate fails.

### Evidence safety

* Given audit and evidence records, when reviewers access them, then least privilege, redaction, retention, and separation from sampled telemetry are enforced.

## Source

FR-018 and CR-001 through CR-008 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS029 - Relationships

* IS029 - sub-issue-of - {{TEMP-6}}: Observability and evidence

## IS030 - Create - Azure deployment story

* IS030 - issue_number: {{TEMP-30}}
* IS030 - title: feat(azure): deploy the API and two Foundry model aliases
* IS030 - state: open
* IS030 - labels: User Story, P0-must-have, P0, infrastructure
* IS030 - milestone: MVP Sprint
* IS030 - assignees: none

### IS030 - body

```markdown
## User Story

As a platform operator, I want the stateless API and two model tiers deployed independently so that application releases and model lifecycle changes remain decoupled.

## Acceptance Criteria

### Application runtime

* Given an approved Azure environment, when deployment completes, then the stateless TokenNexus API runs on Azure Container Apps with immutable revisions and at least one replica in timed evaluation and release environments.

### Model serving

* Given two approved Microsoft Foundry serverless deployments, when aliases resolve, then `economical` and `capable` invoke the configured physical deployments without exposing physical names in the public contract.
* Given subscription, region, deployment type, quota, capacity, lifecycle, networking, or data-processing policy fails validation, when deployment is attempted, then promotion is blocked with an actionable result.

## Source

Dependencies, Operational Considerations, and Rollout and Release Plan in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS030 - Relationships

* IS030 - sub-issue-of - {{TEMP-7}}: Azure MVP runtime

## IS031 - Create - Identity and settings story

* IS031 - issue_number: {{TEMP-31}}
* IS031 - title: feat(identity): configure managed identity, RBAC, and versioned settings
* IS031 - state: open
* IS031 - labels: User Story, P0-must-have, P0, infrastructure
* IS031 - milestone: MVP Sprint
* IS031 - assignees: none

### IS031 - body

```markdown
## User Story

As a platform operator, I want managed identity and versioned environment configuration so that the runtime accesses approved resources without embedded credentials and decisions remain reproducible.

## Acceptance Criteria

### Least privilege

* Given the deployed runtime identity, when it accesses models, state, cache, telemetry, secrets, and audit sinks, then only required data-plane operations succeed and unauthorized operations fail.
* Given application configuration, when source and deployment outputs are scanned, then credentials are externalized and no secret value is committed or rendered.

### Versioned configuration

* Given policy, pricing, evaluator, cache, session, model alias, content-filter, and telemetry settings, when a request is admitted, then immutable version identifiers are captured with its policy snapshot.

## Source

FR-014, FR-016, and Operational Considerations in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS031 - Relationships

* IS031 - sub-issue-of - {{TEMP-7}}: Azure MVP runtime

## IS032 - Create - Rollback and capacity story

* IS032 - issue_number: {{TEMP-32}}
* IS032 - title: feat(operations): validate rollback, capacity, and controlled failure
* IS032 - state: open
* IS032 - labels: User Story, P0-must-have, P0, infrastructure
* IS032 - milestone: MVP Sprint
* IS032 - assignees: none

### IS032 - body

```markdown
## User Story

As a service operator, I want tested rollback and capacity evidence so that failed revisions, model changes, quotas, and dependency outages have controlled recovery paths.

## Acceptance Criteria

### Rollback

* Given a failed application revision or alias promotion, when rollback is initiated, then the last approved revision and model mapping are restored and the transition is audited.

### Capacity and failure

* Given the release environment, when capacity validation runs, then model quota, deployability, concurrency, cache availability, minimum replicas, and secondary deployment procedure are recorded.
* Given provider, evaluator, cache, or telemetry timeouts, when fault tests run, then bounded retries, circuit breakers, cancellation, and truthful degraded or failed outcomes match policy.

## Source

NFR-004 and Operational Considerations in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS032 - Relationships

* IS032 - sub-issue-of - {{TEMP-7}}: Azure MVP runtime

## IS033 - Create - Deterministic test harness story

* IS033 - issue_number: {{TEMP-33}}
* IS033 - title: test(core): create deterministic contract and policy test harness
* IS033 - state: open
* IS033 - labels: User Story, P0-must-have, P0, general-agent
* IS033 - milestone: MVP Sprint
* IS033 - assignees: none

### IS033 - body

```markdown
## User Story

As a delivery engineer, I want deterministic substitutes for every integration so that policy behavior can be proven before Azure dependencies are available.

## Acceptance Criteria

### Deterministic fixtures

* Given fake clocks, IDs, model aliases, evaluator, cache, pricing, tools, journal, identity, and telemetry sink, when the same test manifest runs twice, then route, budget, cache, evaluation, escalation, status, reason codes, and exact call counts are identical.
* Given canonical JSON fixtures, when supported runtimes hash admitted intent, then each produces the same RFC 8785 SHA-256 fingerprint.

### Cross-record invariants

* Given generated event sequences, when property tests run, then paid operations always have reservations, attempts never exceed two, escalation never exceeds one, terminal records remain immutable, and cancellation or deadline prevents new work.

## Source

NFR-007 and NFR-012 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS033 - Relationships

* IS033 - sub-issue-of - {{TEMP-8}}: MVP validation

## IS034 - Create - End-to-end acceptance story

* IS034 - issue_number: {{TEMP-34}}
* IS034 - title: test(mvp): automate the eight end-to-end acceptance scenarios
* IS034 - state: open
* IS034 - labels: User Story, P0-must-have, P0, general-agent
* IS034 - milestone: MVP Sprint
* IS034 - assignees: none

### IS034 - body

```markdown
## User Story

As a product owner, I want the eight required journeys automated end to end so that MVP acceptance is based on repeatable evidence rather than demonstrations.

## Acceptance Criteria

### Required scenarios

* Given the frozen evaluation manifest, when the suite runs, then a routine request routes economically, a complex or critical request routes capably, and low quality escalates once.
* Given cache, budget, and authorization fixtures, when the suite runs, then an eligible paraphrase is reused, an over-budget request is governed, and an unauthorized action is denied without losing non-sensitive input.
* Given policy and adversarial fixtures, when the suite runs, then an authorized policy change is confirmed, versioned, and audited, and a disallowed tool or seeded-secret disclosure is prevented.

### Evidence

* Given any required scenario fails or lacks linked execution and control evidence, when the MVP gate is evaluated, then release acceptance fails.

## Source

Required Acceptance Scenarios 1-8 and MVP Exit Rule in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS034 - Relationships

* IS034 - sub-issue-of - {{TEMP-8}}: MVP validation

## IS035 - Create - Performance and accessibility story

* IS035 - issue_number: {{TEMP-35}}
* IS035 - title: test(quality): verify performance, accessibility, and release gates
* IS035 - state: open
* IS035 - labels: User Story, P1-should-have, general-agent
* IS035 - milestone: none
* IS035 - assignees: none

### IS035 - body

```markdown
## User Story

As an end user, I want a responsive and accessible client so that routine work can be completed efficiently with keyboard and assistive technology.

## Acceptance Criteria

### Performance

* Given at least 20 timed eligible requests, when orchestration latency is measured separately, then p95 overhead is no more than 500 ms.
* Given at least 20 non-cached, non-escalated release-environment requests excluding documented provider outages, when end-to-end latency is measured, then at least 95% complete within 10 seconds.

### Accessibility

* Given the reference client, when automated WCAG 2.1 AA checks and a manual keyboard walkthrough run, then controls have meaningful labels, visible focus, keyboard operation, and compliant color contrast.

## Source

NFR-005, NFR-006, and NFR-009 in `docs/prds/tokennexus-ai-framework-prd.md`.
```

### IS035 - Relationships

* IS035 - sub-issue-of - {{TEMP-8}}: MVP validation

## Similarity Gate Before Execution

No similarity category is assigned because no GitHub search was permitted. Before any Create operation, search the confirmed repository using each title's core noun phrase and PRD requirement terms, hydrate plausible matches, and record Match, Similar, Distinct, or Uncertain. Parent issues must be created before child issues, and sub-issue links must be applied only after temporary IDs resolve to actual issue numbers.

<!-- markdown-table-prettify-ignore-end -->