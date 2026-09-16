<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Discovery Issue Analysis - TokenNexus-AI-Framework

* **Artifacts**: docs/prds/tokennexus-ai-framework-prd.md; internal architecture research summarized below
* **Repository**: TokenNexus-AI/TokenNexus-AI (provisional; verify before execution)
* **Proposed Milestone**: MVP Sprint (P0 stories only; verify before execution)
* **Mode**: Manual, planning only. No GitHub API calls or mutations were made.

## Architecture Constraints Applied

* Keep routing, budget, authorization, quality, escalation, and terminal-state authority in a deterministic application-owned coordinator.
* Use Draft 2020-12 schemas, Semantic Versioning, UUIDv7 IDs, RFC 8785 fingerprints, canonical decimal strings, RFC 3339 UTC timestamps, and a closed dotted public reason-code registry.
* Keep request content in process, persist only structured non-sensitive session recovery state, and separate semantic cache storage from conversation state.
* Put an application-owned capability facade between specialists and protected tools; specialists receive no reusable credentials.
* Host the stateless API on Azure Container Apps and resolve two Microsoft Foundry serverless model deployments through `economical` and `capable` aliases.
* Export metadata-only OpenTelemetry to Application Insights while retaining the execution journal and security audit records as unsampled authoritative evidence.
* Treat pilot values such as quality threshold 4/5, semantic distance 0.05, cache TTL 60 seconds, and session TTLs as versioned calibration inputs, not production commitments.

## Label Plan

| Label | Applies To | Purpose |
|-------|------------|---------|
| Epic | Parent issues | Groups related product outcomes |
| User Story | Child issues | Represents independently testable user value |
| P0-must-have | MVP epics and stories | Required for MVP exit or foundational to a Must requirement |
| P1-should-have | Deferred stories | Supports Should requirements after MVP-critical work |
| P2-future | Future stories | Explicitly deferred capability |
| P0 | MVP stories only | Requested MVP implementation marker |
| billing-agent | Economics issues | Routing, cost, budget, and pricing policy |
| technical-agent | Runtime issues | Models, cache, quality, and protected tools |
| general-agent | Product issues | Contracts, orchestration, client, and session behavior |
| infrastructure | Platform issues | Azure runtime, identity, configuration, and release operations |
| observability | Evidence issues | Telemetry, reporting, audit, and compliance evidence |

## Planned Epics

| ID | Temporary ID | Working Title | Priority | Domain | Child Stories | Epic Acceptance Outcome |
|----|--------------|---------------|----------|--------|---------------|-------------------------|
| IS001 | {{TEMP-1}} | feat(core): establish governed request orchestration | P0-must-have | general-agent | IS009-IS011 | Given the P0 children are complete, when a valid or invalid request runs, then the coordinator produces one bounded, replay-safe terminal outcome. |
| IS002 | {{TEMP-2}} | feat(economics): govern routing and request budgets | P0-must-have | billing-agent | IS012-IS014 | Given approved policy and pricing, when a request is evaluated, then only an eligible and funded execution path can start. |
| IS003 | {{TEMP-3}} | feat(quality): control cache, evaluation, and escalation | P0-must-have | technical-agent | IS015-IS018 | Given model or cache candidates, when quality controls run, then reuse and escalation remain scoped, explainable, and bounded. |
| IS004 | {{TEMP-4}} | feat(security): enforce protected specialist and tool actions | P0-must-have | technical-agent | IS019-IS021 | Given untrusted content or a protected proposal, when authorization runs, then only a constrained approved action can execute without exposing secrets. |
| IS005 | {{TEMP-5}} | feat(client): deliver the request workspace and recoverable sessions | P0-must-have | general-agent | IS022-IS025 | Given an authenticated user, when routine and denied journeys run, then work remains usable, explainable, and recoverable. |
| IS006 | {{TEMP-6}} | feat(evidence): provide economics observability and control evidence | P0-must-have | observability | IS026-IS029 | Given completed requests and protected actions, when evidence is inspected, then economics, quality, control, and trace records are complete and safe. |
| IS007 | {{TEMP-7}} | feat(platform): deploy the Azure MVP runtime | P0-must-have | infrastructure | IS030-IS032 | Given an approved Azure environment, when the MVP is deployed or rolled back, then aliases, identity, configuration, and capacity remain reproducible. |
| IS008 | {{TEMP-8}} | test(mvp): prove release acceptance and quality gates | P0-must-have | general-agent | IS033-IS035 | Given the frozen evaluation manifest, when release validation runs, then every Must requirement and required scenario has reproducible evidence. |

## Planned User Stories

| ID | Temporary ID | Working Title | Priority Labels | Domain | PRD Coverage | Given/When/Then Acceptance Outcome |
|----|--------------|---------------|-----------------|--------|--------------|------------------------------------|
| IS009 | {{TEMP-9}} | feat(api): publish versioned request and result contracts | P0-must-have, P0 | general-agent | FR-001, FR-019, NFR-003 | Given valid and invalid envelopes, when they cross the API boundary, then schemas normalize valid input and return field-specific RFC 9457 errors for invalid input. |
| IS010 | {{TEMP-10}} | feat(core): implement deterministic coordinator and idempotency journal | P0-must-have, P0 | general-agent | FR-007, NFR-007, NFR-012 | Given replay, cancellation, timeout, and escalation cases, when the workflow reduces events, then it performs no duplicate paid work, no work after terminal state, and at most two quality attempts. |
| IS011 | {{TEMP-11}} | feat(models): add provider-neutral model adapters and deterministic substitutes | P0-must-have, P0 | technical-agent | FR-012, NFR-007, NFR-008 | Given economical and capable aliases or test doubles, when either adapter runs, then the public contract and policy domain remain unchanged. |
| IS012 | {{TEMP-12}} | feat(routing): select eligible models with versioned policy | P0-must-have, P0 | billing-agent | FR-002 | Given labeled routine, complex, and critical requests, when policy runs, then at least 90% select the expected alias with a policy version and public reason codes. |
| IS013 | {{TEMP-13}} | feat(budget): estimate cost and enforce request budget actions | P0-must-have, P0 | billing-agent | FR-003, NFR-012 | Given requests above and below their budget, when admission runs, then disallowed paid paths never start and the result records downgrade, approval, or block. |
| IS014 | {{TEMP-14}} | feat(policy): administer confirmed versioned policy changes | P0-must-have, P0 | billing-agent | FR-011, acceptance scenario 7 | Given an authorized confirmed change, when policy is updated, then a new version and audit event affect subsequent requests while rollback remains possible. |
| IS015 | {{TEMP-15}} | feat(cache): implement scoped semantic response reuse | P0-must-have, P0 | technical-agent | FR-005, NFR-002 | Given approved paraphrases and bypass cases, when cache lookup runs, then eligible hits avoid model calls and stale, sensitive, or cross-scope content never returns. |
| IS016 | {{TEMP-16}} | feat(quality): evaluate every non-cached response | P0-must-have, P0 | technical-agent | FR-006 | Given deterministic checks and a versioned judge, when a non-cached response completes, then its score, threshold, evaluator version, and availability state are recorded. |
| IS017 | {{TEMP-17}} | feat(escalation): retry low-quality output once when eligible | P0-must-have, P0 | technical-agent | FR-007, FR-008, NFR-012 | Given a below-threshold result, when policy, budget, and deadline permit or deny escalation, then one linked higher-tier attempt runs or a controlled quality-unmet result returns. |
| IS018 | {{TEMP-18}} | feat(runtime): return controlled degraded outcomes | P1-should-have | technical-agent | FR-013, NFR-004 | Given evaluator, cache, provider, or telemetry enrichment failure, when routine inference can continue safely, then a bounded truthful degraded result identifies component status without leaking internals. |
| IS019 | {{TEMP-19}} | feat(auth): enforce server-side roles for protected actions | P0-must-have, P0 | technical-agent | FR-016, NFR-010 | Given authorized and unauthorized actors, when policy, export, or cache actions are requested, then server-side checks deny and audit all unauthorized cases independently of client visibility. |
| IS020 | {{TEMP-20}} | feat(tools): mediate bounded specialist tool calls | P0-must-have, P0 | technical-agent | FR-020, NFR-012 | Given adversarial proposals and one-use grants, when a specialist proposes a tool call, then the capability facade validates identity, arguments, budget, approval, and receipts before dispatch. |
| IS021 | {{TEMP-21}} | feat(privacy): externalize secrets and minimize retained content | P0-must-have, P0 | technical-agent | FR-014, NFR-001, NFR-002 | Given source, runtime traces, sessions, and cache records, when scans and canary tests run, then credentials are absent and raw content persistence remains off or redacted by default. |
| IS022 | {{TEMP-22}} | feat(client): build the usable request workspace | P0-must-have, P0 | general-agent | PRD 5, journeys 1-6 | Given an authenticated user, when the first screen opens and a request runs, then input, constraints, execution, response, decision details, feedback entry point, and errors are operable. |
| IS023 | {{TEMP-23}} | feat(session): preserve non-sensitive work across interruptions | P0-must-have, P0 | general-agent | FR-017, NFR-011 | Given a valid session or authorization denial, when the user resumes, then at least nine of ten journeys avoid repeated authentication and retain only non-sensitive work with one recovery action. |
| IS024 | {{TEMP-24}} | feat(explainability): present safe decision summaries | P0-must-have, P0 | general-agent | FR-019, NFR-003 | Given completed, cached, escalated, or blocked outcomes, when results render, then approved aliases, cost, latency, quality, cache, escalation, and public reason codes appear without hidden data. |
| IS025 | {{TEMP-25}} | feat(feedback): record explicit user ratings | P2-future | general-agent | FR-015 | Given a completed request, when a user submits a rating, then it is linked to the request without automatically mutating policy. |
| IS026 | {{TEMP-26}} | feat(journal): persist immutable execution economics records | P0-must-have, P0 | observability | FR-009 | Given a terminal request, when its record is projected, then every required policy, token, cost, latency, quality, cache, escalation, and tool field passes schema validation. |
| IS027 | {{TEMP-27}} | feat(telemetry): export metadata-only OpenTelemetry traces and metrics | P0-must-have, P0 | observability | G-005, NFR-001, NFR-003 | Given an accepted request, when components execute, then correlated standard GenAI and `tokennexus.*` spans export without raw content and metrics avoid high-cardinality dimensions. |
| IS028 | {{TEMP-28}} | feat(reporting): compare MVP economics with the all-frontier baseline | P0-must-have, P0 | observability | FR-010, G-002 | Given at least 30 paired requests under frozen assumptions, when reporting runs, then routing, tokens, cost, latency, quality, cache, and escalation comparisons are reproducible. |
| IS029 | {{TEMP-29}} | feat(compliance): assemble the MVP evidence catalog | P0-must-have, P0 | observability | FR-018, CR-001-CR-008 | Given the eight applicable controls, when release evidence is assembled, then each control links a named artifact or an approved non-applicable rationale. |
| IS030 | {{TEMP-30}} | feat(azure): deploy the API and two Foundry model aliases | P0-must-have, P0 | infrastructure | Dependencies, rollout | Given approved subscription, region, and models, when infrastructure deploys, then Container Apps invokes two Foundry serverless deployments through stable aliases with deterministic substitutes available. |
| IS031 | {{TEMP-31}} | feat(identity): configure managed identity, RBAC, and versioned settings | P0-must-have, P0 | infrastructure | FR-014, FR-016, operations | Given environment-specific configuration, when the runtime starts, then secrets remain external, least-privilege data-plane access succeeds, and policy, pricing, evaluator, cache, and model settings are versioned. |
| IS032 | {{TEMP-32}} | feat(operations): validate rollback, capacity, and controlled failure | P0-must-have, P0 | infrastructure | NFR-004, release-ready gate | Given a prior healthy revision and injected dependency failures, when rollback or recovery runs, then service returns to the approved version and records quota, concurrency, timeout, and secondary-deployment evidence. |
| IS033 | {{TEMP-33}} | test(core): create deterministic contract and policy test harness | P0-must-have, P0 | general-agent | NFR-007 | Given fake clocks, IDs, models, evaluator, cache, pricing, tools, journal, identity, and telemetry, when tests repeat, then routing and reason-code outcomes are stable with exact call counts. |
| IS034 | {{TEMP-34}} | test(mvp): automate the eight end-to-end acceptance scenarios | P0-must-have, P0 | general-agent | Acceptance scenarios 1-8 | Given the frozen manifest and test environment, when the suite runs, then all eight required scenarios pass and produce linked evidence. |
| IS035 | {{TEMP-35}} | test(quality): verify performance, accessibility, and release gates | P1-should-have | general-agent | NFR-005, NFR-006, NFR-009 | Given representative traffic and the reference client, when release checks run, then latency, orchestration overhead, keyboard use, focus, labels, and contrast meet their targets. |

## P0 Coverage Check

| Required Surface | Planned P0 Stories | Status |
|------------------|--------------------|--------|
| Must functional requirements FR-001-FR-003, FR-005-FR-010, FR-014, FR-016-FR-020 | IS009-IS010, IS012-IS013, IS015-IS017, IS019-IS021, IS023-IS024, IS026, IS028-IS029 | Covered |
| Must non-functional requirements NFR-001-NFR-003, NFR-007, NFR-010-NFR-012 | IS009-IS010, IS015, IS019-IS021, IS023-IS024, IS026-IS027, IS033 | Covered |
| Required acceptance scenarios 1-8 | IS034 plus owning implementation stories | Covered |
| Two model tiers and deterministic substitutes | IS011, IS030, IS033 | Covered |
| MVP client and evidence inventory | IS022, IS026-IS029 | Covered |

## Similarity Status

Similarity assessment is intentionally deferred because the user prohibited GitHub operations and no local issue export exists. Before issue creation, execution must authenticate, search the target repository by each candidate's key terms, hydrate plausible matches, and classify them as Match, Similar, Distinct, or Uncertain. No candidate is safe to create until that check completes.

## Open Review Decisions

* Confirm the repository owner/name and whether `MVP Sprint` should be created or replaced by an existing milestone.
* Confirm whether the repository accepts both `P0-must-have` and the additional `P0` marker on MVP stories.
* Confirm whether all eight epics should carry P0 priority even when they contain deferred P1/P2 children.
* Resolve PRD questions Q-001 through Q-009 before stories that require owner-approved production values can close.

<!-- markdown-table-prettify-ignore-end -->