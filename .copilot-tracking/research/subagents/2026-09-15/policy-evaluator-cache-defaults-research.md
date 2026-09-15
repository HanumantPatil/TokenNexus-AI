---
title: Policy, Evaluator, and Cache Defaults Research
description: Evidence and calibration guidance for defensible TokenNexus-AI-Framework MVP policy defaults
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: research
---

## Research Scope

* Evaluator design and unavailable-evaluator behavior
* Semantic cache similarity, time-to-live, and scope
* Context optimization and session retention
* Request budget, latency, transient retry, and one-step escalation behavior
* Approval, block, and downgrade policy
* Calibration protocol for a 30-request evaluation set
* Normative architecture defaults versus domain-calibrated values requiring owner approval

## Executive Recommendation

Adopt a small set of strict, versioned pilot defaults while preserving the
PRD's owner approval gates. The defaults in this document are suitable for
building deterministic fixtures and running a controlled MVP pilot. They are
not production service levels or universal quality thresholds.

The central rule is that deterministic policy remains authoritative. An LLM
evaluator may inform the one allowed quality escalation, but it cannot grant
authorization, increase a budget, extend a deadline, admit cache content, or
override a deterministic safety or schema failure.

Use the following initial profile:

| Control | MVP pilot default | Classification |
| --- | --- | --- |
| Quality gate | All deterministic checks pass and rubric score is at least 4 on a 1-5 scale | Provisional |
| Evaluator unavailable | Return a valid routine response as `degraded`; do not infer low quality or escalate | Hard behavior |
| Cache similarity | Maximum APIM semantic distance of `0.05` | Provisional |
| Cache TTL | 60 seconds | Provisional |
| Cache scope | Tenant, application, use case, policy, model, embedding, authorization cohort, locale, and freshness class | Hard minimum |
| Cache bypass | Sensitive, personalized, freshness-critical, tool-bearing, non-final, degraded, or policy-disallowed content | Hard behavior |
| Provider conversation storage | Disabled | Hard MVP behavior |
| Session state | Structured non-sensitive fields only; no transcript or rolling summary by default | Hard MVP behavior |
| Session TTL | 30-minute inactivity limit and 8-hour absolute limit | Provisional |
| Model input | 8,192 tokens maximum, including mandatory context | Provisional |
| Model output | 1,024 tokens maximum | Provisional |
| Context history | Current turn plus at most two prior user-assistant turn pairs | Provisional |
| End-to-end deadline | 10 seconds, never reset | PRD invariant |
| Orchestration overhead | 500 ms p95 excluding model, embedding, and external tool time | PRD invariant |
| Quality escalation | At most one higher-tier attempt | PRD invariant |
| Transient retry | One centralized same-operation retry allowance per request | Provisional |
| Tool calls | One bounded product-tool call per attempt | Provisional |
| Over-budget behavior | Downgrade only when all quality and policy gates still pass; otherwise approval or block | Hard behavior |
| Circuit breaker | Open after 5 consecutive failures or at least 50% failures in 10 calls; probe after 30 seconds | Provisional |

Every provisional value must live in versioned configuration, appear in the
evaluation manifest, and remain subject to calibration and accountable-owner
approval. Changing one creates a new policy version and invalidates direct
comparison with runs made under the previous version.

## Decision Classification

### Hard Invariants

These values or behaviors follow directly from the PRD and should not be
weakened by calibration:

* One immutable request ID spans cache, model attempts, evaluation, and final
    outcome.
* There are no more than two quality attempts and no more than one escalation.
* One absolute request deadline governs all work and is not renewed by retries,
    escalation, approval resume, or dependency recovery.
* No paid or side-effecting operation starts without sufficient reserved
    budget, time, authorization, and idempotency evidence.
* Unknown or invalid constraints fail before execution with an actionable
    status.
* Sensitive and freshness-critical requests bypass semantic-cache lookup and
    store.
* Raw prompts, responses, hidden instructions, credentials, and tool payloads
    are not persisted or exported by default.
* Protected actions deny when authorization, policy, evaluator, or required
    audit evidence is unavailable.
* Routine inference may return a bounded degraded result when an optional
    evaluator, cache, or telemetry enrichment dependency fails.
* SDK retry layers are disabled or made visible to the coordinator. Retries
    cannot multiply across gateway, client, SDK, and service layers.
* Deterministic substitutes must reproduce route, budget, cache, evaluator,
    escalation, and reason-code decisions.

### Provisional Trial Defaults

The numerical profile above is deliberately conservative. It creates a
repeatable starting point and limits blast radius while the reference domain,
models, prices, and traffic remain unknown. Passing a pilot under these values
does not establish that the values are optimal.

### Decisions That Remain Open

The following cannot be selected honestly from generic vendor guidance:

* Dollar-denominated request caps and approval thresholds
* The two physical model deployments and their token limits
* Domain rubric wording and the relative importance of rubric dimensions
* Production latency objectives and component timeout allocations
* Production concurrency, queues, breaker windows, and regional failover
* Cache TTLs for domain data with explicit freshness guarantees
* Session retention where personal or regulated data applies
* Production false-positive and false-negative tolerances

These remain owner decisions under PRD questions Q-003 through Q-009.

## Evaluator Policy

### Selected Shape

Use a two-layer evaluator rather than a general writing-quality score alone:

1. Run deterministic checks for schema validity, required fields, citations,
     policy compliance, prohibited disclosure, bounded tool behavior, and any
     domain assertions that can be computed.
2. Run one versioned LLM-as-judge rubric for the domain qualities that cannot
     be computed directly.
3. Pass only when every hard check passes and the judge score is at least 4.

Foundry general-purpose evaluators use a 1-5 Likert scale and default to a pass
threshold of 3. That is a platform default, not evidence that 3 is sufficient
for TokenNexus. A pilot threshold of 4 is preferable because score 3 is the
middle of an ordinal scale and the product may spend extra budget based on the
decision. Calibration may lower or raise the threshold only after comparison
with domain-owner labels.

The evaluator result must include:

* Evaluator name, rubric version, judge model alias and deployment version
* Score, threshold, pass state, and safe reason codes
* Deterministic-check results and an explicit missing-input state
* Latency, estimated tokens and cost, retry count, and component status
* The attempt ID evaluated and the evaluation-run identifier

Do not average away a failed hard check. An answer with fluent prose but an
invalid citation, disallowed disclosure, or missing required action remains a
failure regardless of its judge score.

### Evaluator Failure Matrix

| Condition | Routine inference | Protected or side-effecting action |
| --- | --- | --- |
| Deterministic check fails | Do not pass; consider one eligible quality escalation | Block the action |
| Judge returns score below 4 | Consider one eligible quality escalation | Block unless a separately defined approval path applies |
| Judge times out or is unavailable | Return valid model output as `degraded`, quality `unknown`; no quality escalation | Fail closed and block |
| Judge output is malformed | One transient retry if the request retry allowance remains, then treat as unavailable | Fail closed and block |
| Required evaluation input is absent | Return `quality_unavailable_input` and do not claim a pass | Fail closed and block |
| Second-attempt score remains below threshold | Return `quality_unmet`; no third attempt | Block the action |

An unavailable evaluator is not evidence of poor quality. Escalating merely
because the judge failed would convert an observability failure into extra
model spend and could repeat indefinitely during an evaluator outage.

### Calibration Requirement

The domain owner must label each candidate response as acceptable or
unacceptable before inspecting the evaluator result. Record score-to-label
confusion, false-pass and false-fail cases, disagreement reasons, and results
by request class. Do not treat coherence or fluency as factual correctness.

## Semantic Cache Policy

### Lookup and Store Defaults

Use an APIM-compatible semantic distance threshold of `0.05` and TTL of 60
seconds for the first pilot. Microsoft recommends starting with a low value
such as 0.05 and warns that values above 0.2 may create mismatches. The same
documentation stresses workload-specific tuning and warns that semantically
similar reuse can still return incorrect, outdated, or unsafe content.

Set `ignore-system-messages=true` only when the cache key also includes the
system/policy version. Otherwise a system-instruction change could reuse an
answer produced under different rules. Skip conversational caching after more
than two prior turn pairs; multi-turn state raises the chance that apparently
similar prompts have different meanings.

Partition each entry by, at minimum:

* Authenticated tenant and application
* Use-case and data-classification policy
* User or authorization cohort when output can differ by permission
* Policy, prompt-template, model, and embedding versions
* Locale and output-format version
* Freshness class and approved knowledge-snapshot version

Store only final HTTP 200 responses that passed all quality and safety gates.
Do not cache degraded, partially streamed, escalated-but-unverified, approval
pending, error, or tool side-effect responses.

### Mandatory Bypass Rules

Bypass both lookup and store when any of these applies:

* Content is sensitive, personal, confidential, regulated, secret-bearing, or
    of unknown classification.
* The request declares current, live, latest, real-time, or freshness-critical
    behavior.
* The response depends on user identity, entitlements, mutable account state,
    or per-request authorization outside the partition key.
* A tool call, transaction, approval, mutation, or other side effect may occur.
* Mandatory context, citation set, policy, model, embedding, or output schema
    does not match the cached entry version.
* The source answer was degraded, below threshold, manually invalidated, or
    created during dependency failure.

Cache failure is fail-open for eligible routine inference: continue to the
model path under the same deadline and budget. Place rate limiting after cache
lookup so cache outages cannot create uncontrolled backend load. Cache failure
is never permission to omit request budget enforcement.

### Cache Calibration

Measure cache classification, not only hit rate. The labeled matrix must
contain expected equivalent paraphrases and hard negatives that share words
or topic but require different answers. Report true hits, false hits, true
misses, and false misses. A false hit is more severe than a miss because it can
return an incorrect or cross-context answer without invoking the model.

Start at 0.05, then test nearby values against the frozen set. Select the
largest threshold that produces zero false hits in the pilot; if several do,
choose the smallest. Zero pilot false hits is necessary but not sufficient for
production because the sample is small.

## Context and Session Policy

### Context Assembly

Use an 8,192-token maximum input envelope and a 1,024-token output ceiling for
the pilot. Reserve space before dispatch rather than relying on provider
truncation. If mandatory content alone exceeds the input ceiling, return a
controlled `mandatory_context_too_large` status instead of silently removing
instructions or evidence.

Assemble context in this order:

1. System and policy instructions
2. Current user request and normalized constraints
3. Mandatory evidence and citation metadata
4. Structured non-sensitive session constraints
5. At most two prior user-assistant turn pairs
6. Optional retrieved context ranked by relevance and freshness

Remove optional items from the bottom of the list until the estimate fits.
Do not summarize recursively. A rolling summary is absent by default because
it adds cost, can hallucinate commitments, can retain sensitive content, and
can carry stored prompt injection.

The execution record must capture estimated tokens before and after context
optimization, the items removed by category, and confirmation that mandatory
instructions and cited evidence remained present.

### Session Defaults

Keep application-owned structured recovery state for 30 minutes of inactivity
and no more than 8 hours from creation. Access may refresh the inactivity
deadline but never the absolute deadline. These are pilot values, not legal or
security standards.

Retain only opaque IDs, server-derived scope, declared constraints, safe public
decision state, schema and policy versions, timestamps, and deletion status.
Provider conversation storage, durable transcripts, persistent profiles, and
cross-session personal memory remain disabled.

## Budget, Approval, and Block Policy

### Formula-Based Cost Ceiling

Do not invent a dollar cap before Q-004 and Q-006 identify models and prices.
Compute a versioned worst-case request envelope instead:

```text
standard_cap = cache_lookup
                         + economical_attempt(max_input, max_output)
                         + evaluator_attempt

escalation_cap = standard_cap
                             + capable_attempt(max_input, max_output)
                             + evaluator_attempt
```

Include embedding, tool, and regional price components when applicable. The
coordinator reserves `standard_cap` before attempt one and reserves the
increment to `escalation_cap` before attempt two. Actual usage is reconciled
after each dependency returns. Neither a retry nor an escalation can spend an
unreserved amount.

The default token and action ceilings are:

* 8,192 model input tokens per attempt
* 1,024 model output tokens per attempt
* One quality escalation
* One bounded product-tool call per attempt
* One centralized transient retry allowance per request

### Decision Order

1. Exclude routes that cannot meet hard quality, security, capability, or
     deadline constraints.
2. Select the lowest estimated-cost eligible route.
3. If the selected route exceeds the caller's cap, try a cheaper route only if
     it remains eligible under all hard constraints.
4. If no route fits, return `approval_required` only when the caller and use
     case have a configured approval workflow and sufficient time remains.
5. Otherwise return `budget_blocked` without invoking a paid path.

Criticality may make the capable tier eligible or required, but it never
increases the budget implicitly. Approval produces a new auditable allowance;
it does not mutate the original policy snapshot silently.

## Latency, Retry, and Outage Policy

### Deadline Allocation

Use the PRD's 10-second end-to-end deadline as one monotonic absolute
deadline. The 500 ms orchestration objective excludes external model,
embedding, evaluator, and tool time but still requires component timing.

Initial component ceilings are pilot guards rather than reservations:

| Component | Pilot ceiling | Failure behavior |
| --- | --- | --- |
| Cache lookup including embedding | 250 ms | Bypass to model path |
| Policy, pricing, and context work combined | 500 ms p95 | Controlled timeout if deadline is exhausted |
| First model attempt | Up to 7 seconds, bounded by remaining deadline | Retry only under centralized transient policy |
| Evaluator | Up to 1.5 seconds, bounded by remaining deadline | Routine result becomes degraded if unavailable |
| Tool call | Up to 2 seconds, bounded by grant and remaining deadline | Controlled tool failure; no alternate unauthorized tool |

Attempt two may start only when its pessimistic model and evaluator estimate,
plus a 250 ms response-finalization reserve, fit inside the remaining absolute
deadline and cost allowance. This prevents an escalation that is guaranteed
to violate the caller's latency constraint.

### Centralized Retry

Allow at most one same-operation transient retry across remote dependencies
for the entire request. Retry only an allowlisted timeout-before-response,
connection reset, HTTP 408, 429, or retryable 5xx condition. Honor a valid
`Retry-After` value only when it fits the absolute deadline. Otherwise use
full-jitter delay capped between 250 ms and 1 second.

Do not retry:

* Authentication, authorization, validation, policy, or budget denials
* Malformed successful responses unless the evaluator retry allowance is used
* Non-idempotent tool calls without a provider-supported idempotency key
* A model call after a response or usage receipt may have been accepted unless
    duplicate suppression is guaranteed
* Any call when the remaining deadline or budget cannot cover the retry

Quality escalation is not a transient retry and uses a separate one-step
counter. Both operations still consume the same deadline and cost ceiling.

### Circuit Breaker and Bulkhead

Maintain a breaker per deployment and dependency operation. For the pilot,
open it after five consecutive failures, or at least 50% failures after ten
observations. Keep it open for 30 seconds, admit one half-open probe, and close
after two successful probes. These values must be tuned from measured request
rate and recovery behavior.

Bound concurrency per dependency from actual TPM/RPM and downstream capacity.
Do not copy Container Apps scaling defaults into the application policy. Queue
no more than twice the configured dependency concurrency and reject new work
with `capacity_unavailable` when its predicted queue delay cannot fit the
request deadline.

Outage behavior is explicit:

* Economical model unavailable: use capable model only when it is independently
    eligible and still fits budget and deadline; record `primary_unavailable`.
* Capable model unavailable: do not loop back to an already failed economical
    result; return the best valid result as degraded or `quality_unmet`.
* Evaluator unavailable: preserve eligible routine inference as degraded; no
    quality-driven escalation.
* Cache unavailable: bypass under rate limiting.
* Telemetry exporter unavailable: complete routine work, persist the required
    execution record locally or durably, and mark telemetry degraded.
* Authorization, policy, pricing, or required audit store unavailable: fail
    closed before protected or paid work whose allowance cannot be proven.

## Public Reason Codes

Use an allowlisted, versioned public vocabulary. Recommended initial codes are:

* `route_economical_eligible`
* `route_capable_required`
* `cache_hit_equivalent`
* `cache_miss`
* `cache_bypass_sensitive`
* `cache_bypass_freshness`
* `cache_unavailable`
* `quality_passed`
* `quality_unmet`
* `quality_unavailable`
* `escalated_quality`
* `escalation_budget_denied`
* `escalation_deadline_denied`
* `budget_downgraded`
* `budget_approval_required`
* `budget_blocked`
* `capacity_unavailable`
* `dependency_timeout`
* `protected_action_denied`
* `degraded_dependency`

Provider errors, prompts, stack traces, policy expressions, and internal risk
signals stay out of public explanations.

## Thirty-Request Calibration Protocol

### Purpose and Limits

The 30-request run is a pilot calibration and gross-defect screen. It can find
obvious routing, cache, evaluator, budget, or reliability defects. It cannot
demonstrate rare-event safety, production reliability, a stable tail latency,
or a true 90% routing rate with narrow uncertainty.

Use a separate set of deterministic fixtures for invariants. Live model calls
are not suitable for proving exact call counts, no third attempt, denial before
spend, cancellation, idempotency, or secret non-disclosure.

### Manifest Design

Create 30 primary requests with overlapping labels so the set includes at
least five routine, five complex, five critical, five cacheable, and five
over-budget cases as required by the PRD. Also include:

* At least five quality-failure seeds eligible for escalation
* At least five cases where escalation is forbidden by budget or deadline
* At least five sensitive or freshness-critical cache bypasses
* Ten approved paraphrase requests across five source answers
* At least ten cache hard negatives with similar topic or wording
* Dependency-failure tags for evaluator, cache, model, and telemetry fixtures
* Protected-tool and adversarial cases in the deterministic companion suite

Each manifest row freezes request content hash, expected route class, minimum
quality label, cache expectation, budget action, escalation eligibility,
freshness and sensitivity flags, model aliases and versions, price version,
policy version, prompt version, evaluator version, embedding version, random
seed where supported, and environment.

Run TokenNexus and the all-capable baseline against identical primary inputs
and assumptions. Cache experiments require a documented cold seed followed by
warm paraphrase and hard-negative probes; do not compare a warm TokenNexus
cache with an unseeded baseline as if that isolated routing savings.

### Labeling and Blinding

Before execution, a domain owner labels expected route eligibility, response
acceptability, cache equivalence, budget action, and escalation eligibility.
Where possible, a second reviewer labels independently and disagreements are
adjudicated before model/evaluator results are revealed. Record uncertainty
instead of forcing an artificial ground truth.

Human reviewers evaluate paired outputs without seeing model alias, route,
cost, or evaluator score. Randomize left-right presentation. The LLM judge
must not see the expected label or baseline identity.

### Execution Sequence

1. Validate the manifest and deterministic fixture suite.
2. Run all deterministic substitutes twice and require identical decisions.
3. Run a cold-cache live pass in randomized order.
4. Seed only approved source answers that passed all gates.
5. Run paraphrase and hard-negative cache probes.
6. Run the all-capable baseline on the same primary requests.
7. Collect blinded human labels and evaluator outputs.
8. Build confusion matrices and investigate every disagreement.
9. Calculate intervals and publish all exclusions and dependency failures.
10. Freeze a candidate policy version only after owner review.

If the same 30 requests are used to tune thresholds, results after tuning are
training results. They must not be presented as independent validation. Freeze
the resulting policy and run a new, independently labeled confirmation set
before release claims.

### Required Metrics

Report raw counts and denominators, not percentages alone:

* Route confusion by expected and actual tier
* Evaluator confusion against human acceptable/unacceptable labels
* Cache true hits, false hits, true misses, and false misses
* Budget downgrade, approval, block, and leakage counts
* Escalation eligible, attempted, prevented, successful, and still-unmet counts
* Model, evaluator, cache, telemetry, and tool failure outcomes
* Input, output, cached, and avoided tokens
* Estimated cost under TokenNexus and the all-capable baseline
* End-to-end and component latency distributions with raw observations
* Missing telemetry fields and sensitive-canary detections

For binary proportions, use Wilson score intervals or exact binomial intervals.
Do not use an unqualified normal approximation with these small denominators.
For zero observed failures, report the one-sided exact 95% upper bound. Zero
failures in 30 trials still permits a true failure probability of roughly
9.5%; zero in five over-budget tests permits roughly 45%. This is why the
pilot cannot establish production safety.

For paired continuous outcomes such as tokens, cost, and latency, report every
pair, median paired difference, interquartile range, and bootstrap confidence
interval if used. With only 20 timed cases, p95 is effectively an extreme
order statistic; label it an observed pilot p95 rather than a stable service
estimate.

### Pilot Stop Conditions

Do not freeze the candidate policy when any of these occurs:

* Any disallowed paid path or unauthorized tool call executes
* Any raw-content, credential, cross-scope, or sensitive-cache canary leaks
* Any semantic-cache false hit occurs
* Any request creates more than one quality escalation
* Any deterministic suite result changes between repeated runs
* Any required execution-record field is absent
* Evaluator false passes cluster in a material domain category
* A tuned result is presented without disclosing reuse of the calibration set

Routing agreement below the PRD's 90% target, approved paraphrase hits below
80%, or latency misses require analysis and a new policy version, but they do
not justify weakening hard safety invariants.

## Deterministic Companion Fixtures

At minimum, prove these behaviors without live dependencies:

1. A route never exceeds its token or cost reservation.
2. Attempt count never exceeds two and escalation count never exceeds one.
3. An identical idempotent replay creates no new model or tool call.
4. Cancellation or deadline expiry prevents new work and ignores late success.
5. Evaluator unavailability does not cause quality escalation.
6. Cache outage falls through under rate limiting.
7. Sensitive, stale, personalized, and tool-bearing requests bypass cache.
8. Cache scope collisions across tenant, user, policy, model, or embedding fail.
9. A false or malformed evaluator result cannot override deterministic checks.
10. Approval creates a new bounded allowance and cannot reopen an expired run.
11. Breaker open and half-open transitions follow the fake clock exactly.
12. Raw-content and secret canaries appear in no store, log, span, or UI trace.

## Planning Handoff

Implementation planning may adopt this document's hard invariants and
provisional profile as configuration version `pilot-1`. Before live
measurement, the accountable owners must fill in:

* Reference use case, data classes, and labeled rubric
* Model deployments, prices, regional quota, and retirement dates
* Dollar budget caps and approval roles
* Production cache freshness and false-hit tolerance
* Production session retention and deletion requirements
* Traffic forecast, concurrency, capacity, and outage ownership

The first implementation should expose every provisional number through one
validated configuration schema and include it in the execution record. No
default should be hidden in prompt text, SDK behavior, or infrastructure
settings.

## Evidence Register

### Workspace Evidence

* docs/prds/tokennexus-ai-framework-prd.md:134-159 defines the product
    principles and ordered governed flow.
* docs/prds/tokennexus-ai-framework-prd.md:170-189 defines budget action,
    context optimization, semantic cache, quality evaluation, one-step
    escalation, degraded states, session recovery, and bounded tools.
* docs/prds/tokennexus-ai-framework-prd.md:195-206 defines dependency
    timeouts, 500 ms orchestration p95, 10-second end-to-end latency,
    deterministic substitutes, and resource bounds.
* docs/prds/tokennexus-ai-framework-prd.md:210-245 defines the execution
    record, instrumentation events, and the 30-request measurement set.
* docs/prds/tokennexus-ai-framework-prd.md:250-288 identifies evaluator,
    cache, pricing, provider, outage, privacy, and evidence risks.
* docs/prds/tokennexus-ai-framework-prd.md:315-337 defines acceptance
    scenarios and open questions Q-003 through Q-009.
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
    fixes the application-owned control-plane boundary and separates quality
    escalation from transient retry.
* .copilot-tracking/research/subagents/2026-09-15/conversation-memory-research.md
    supports stateless provider calls, structured ephemeral session state, and
    separate memory and cache lifecycles.
* .copilot-tracking/research/subagents/2026-09-15/router-specialist-handoff-research.md
    supports one absolute deadline, coordinator-owned allowances, explicit
    failure states, idempotency, and bounded specialist capabilities.

### External Evidence

* [Microsoft Foundry general-purpose evaluators](https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/evaluation-evaluators/general-purpose-evaluators)
    documents the 1-5 scale, default threshold 3, LLM-as-judge cost, short-output
    reliability caveat, and the fact that coherence and fluency measure writing
    quality rather than factual correctness.
* [Azure AI Evaluation Python API](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation?view=azure-python)
    documents groundedness, relevance, retrieval, task adherence, tool-call
    accuracy, configurable graders, and explicit evaluator-error behavior.
* [APIM semantic-cache lookup](https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy)
    documents distance threshold semantics, the 0.05 starting point, mismatch
    risk above 0.2, `vary-by`, conversation limits, sensitive-use caution,
    Prompt Shields, and rate limiting after lookup.
* [APIM semantic-cache store](https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-store-policy)
    documents explicit TTL, HTTP 200 storage behavior, and non-failing cache
    operations.
* [Azure Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)
    supports bounded retries, idempotency analysis, jittered delay, cancellation,
    operation-context ownership, and avoidance of nested retry layers.
* [Azure Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
    supports closed, open, and half-open states, cautious recovery probes, and
    workload-calibrated thresholds.
* [Azure Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
    supports dependency isolation and bounded concurrency.
* [Azure OpenAI quota and limits](https://learn.microsoft.com/en-us/azure/ai-services/openai/quotas-limits)
    documents TPM/RPM capacity controls and reinforces sizing from selected
    deployment quota rather than generic app defaults.
* [Azure OpenAI latency](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/latency)
    explains that latency depends on model, prompt, generated tokens, and
    workload, so production component timeouts require measurement.
* [Azure Container Apps scale](https://learn.microsoft.com/en-us/azure/container-apps/scale-app)
    documents platform defaults but does not make them suitable application
    capacity guarantees.
* [NIST binomial proportion confidence intervals](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/binomial.htm)
    supports Wilson and exact intervals for small binomial samples rather than
    relying on normal approximations.
* [OWASP LLM10: Unbounded Consumption](https://genai.owasp.org/llmrisk/llm102025-unbounded-consumption/)
    supports bounded inputs, tokens, requests, queues, timeouts, quotas,
    monitoring, and graceful degradation.
* [OWASP LLM08: Vector and Embedding Weaknesses](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)
    supports permission-aware partitioning, trusted-source validation, and
    monitoring for retrieval and cache systems.

## Follow-On Questions

* After the use case is selected, what rubric dimensions predict human
    acceptance better than the general writing-quality evaluators?
* Which pair of model deployments can satisfy the 10-second deadline under
    the selected region's quota and observed output lengths?
* What threshold sweep around 0.05 produces zero cache false hits on a larger,
    independent hard-negative set?
* What sample size is required for the production false-hit, budget-leakage,
    route-error, and protected-action risk tolerances?
* Which cost and latency distributions should drive concurrency and breaker
    tuning after the pilot?

## Clarifying Questions

* Who owns final approval for quality, budget, cache, privacy, and operations?
* What reference domain, risk class, jurisdiction, and data classification
    apply?
* Which models, region, pricing date, traffic forecast, and operating budget
    should parameterize the formula-based ceilings?
* Does the 10-second target include both model attempts and both evaluator
    calls for escalation cases, or only the non-escalated population described
    by NFR-006?
* Is an evaluator outage allowed to return a routine answer to the selected
    client, and which request classes must fail closed?
* What independent confirmation set will be funded after the 30-request
    calibration pilot?
