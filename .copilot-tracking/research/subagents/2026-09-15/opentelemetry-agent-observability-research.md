---
title: OpenTelemetry Agent Observability Research
description: Research on OpenTelemetry observability patterns for TokenNexus-AI-Framework agent systems
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: concept
---

## Research Scope

* Map TokenNexus-AI-Framework request, policy, cache, model, evaluator, escalation, and tool activity to traces and spans
* Define metrics for cost, tokens, latency, cache behavior, quality, and budgets
* Define structured logging, correlation, retry and handoff links, baggage, sampling, privacy, redaction, and cardinality controls
* Evaluate collector and export topologies with Azure Monitor and Application Insights integration
* Define evidence reporting and tests for telemetry completeness and sensitive-data leakage
* Evaluate alternatives and recommend an MVP pattern

## Status

Complete. The recommendation covers the MVP observability contract and identifies
the decisions that still require implementation-time validation.

## PRD Evidence

The design treats the PRD execution record as a durable product record and
OpenTelemetry as correlated operational evidence. Telemetry loss or sampling must
not change routing, budget, quality, authorization, or audit behavior.

| PRD requirement | Observability implication |
| ----------------- | --------------------------- |
| G-005 and FR-002 | Record the policy version, selected model alias, and stable reason codes for every completed evaluation request. |
| FR-003 | Observe the estimate and resulting `allow`, `downgrade`, `block`, or `approval_required` action before any paid attempt. |
| FR-005 | Distinguish hit, miss, and bypass, including bounded entry age and avoided-token estimates without recording cache keys or content. |
| FR-006 through FR-008 | Correlate every model attempt with its evaluation and record whether one permitted escalation occurred or why it did not. |
| FR-009 | Validate the durable execution record independently, then put its request ID on telemetry for investigation. |
| FR-010 | Identify the evaluation manifest, cohort, and baseline mode so paired reports use identical assumptions. |
| FR-013 | Make evaluator, provider, cache, and telemetry degradation visible without turning optional enrichment failures into request failures. |
| FR-014, NFR-001, and NFR-002 | Keep raw prompts, responses, tool arguments, tool results, credentials, and personal data out of production telemetry by default. |
| FR-015 | Correlate feedback to the request without attaching free-form feedback text or mutating policy. |
| FR-016 and FR-020 | Produce security audit evidence for protected and tool actions independently of trace sampling. |
| FR-019 and NFR-003 | Use the same allowlisted public reason-code vocabulary in the decision summary and telemetry. |
| NFR-004 through NFR-006 | Separate orchestration, provider, evaluator, cache, and tool latency so reliability and p95 targets are measurable. |
| NFR-007 and FR-012 | Keep instrumentation independent of provider adapters and test it with deterministic dependencies and in-memory exporters. |
| NFR-012 | Observe token, cost, escalation, tool-call, cancellation, and timeout bounds. |
| CR-001 through CR-008 | Link versioned evidence artifacts and test-run identifiers without putting evidence bodies in span attributes. |

Primary local evidence is in `docs/prds/tokennexus-ai-framework-prd.md`, especially
sections 4, 6, 7, 8, 11, and 12.

## Findings

### Design Principles

* Start one distributed trace when a valid request is accepted. Make all synchronous
  decision work a descendant of that request span.
* Use W3C Trace Context for parentage and W3C Baggage only for a very small,
  allowlisted set of cross-process routing dimensions.
* Prefer current OpenTelemetry semantic conventions. Use `gen_ai.*` only with the
  meaning and type defined by the installed convention version.
* Put TokenNexus-only policy, economics, cache, quality, and control data in a
  versioned `tokennexus.*` namespace.
* Use attributes for queryable state, events for meaningful state transitions,
  links for causal work that is not nested, metrics for aggregates, and structured
  logs for diagnostic or audit records.
* Never depend on sampled trace data for a durable execution record, authorization
  evidence, budget enforcement, or billing reconciliation.
* Use low-cardinality identifiers on metrics. Request, attempt, response, user,
  session, and cache-entry identifiers belong only on traces, logs, or the durable
  record.

### Canonical Trace Model

Use instrumentation scope `TokenNexus.Observability` with a schema URL or resource
attribute such as `tokennexus.telemetry.schema.version=1.0.0`. Framework-emitted
Agent Framework spans can remain under their native instrumentation scope.

| Span name | Kind | Parent or link | Required purpose |
| ----------- | ------ | ---------------- | ------------------ |
| `POST /requests` or framework server route | `SERVER` | Incoming remote context | HTTP boundary and transport outcome. Keep framework route naming rather than raw URLs. |
| `tokennexus.request` | `INTERNAL` | Server span | One accepted business request from validation through the final controlled outcome. |
| `tokennexus.policy.evaluate` | `INTERNAL` | Request span | Eligibility, route, cost estimate, budget action, policy version, and reason codes. |
| `tokennexus.cache.lookup` | `INTERNAL` | Request span | Cache hit, miss, or bypass and eligible avoided work. |
| `chat {model}` | `CLIENT` | Request span | One provider model attempt using current GenAI client conventions. Prefer framework or provider instrumentation over a duplicate wrapper span. |
| `tokennexus.quality.evaluate` | `INTERNAL` | Attempt or request span | Evaluator outcome, threshold, version, and unavailable state. |
| `tokennexus.escalation.evaluate` | `INTERNAL` | Request span | Whether the single escalation is allowed and the stable public reason. |
| `execute_tool {tool}` | Framework-defined, normally `INTERNAL` or `CLIENT` | Invoking agent or request span | One configured tool call with bounded-path and authorization outcome. Do not duplicate a framework-emitted tool span. |
| `tokennexus.protected_action` | `INTERNAL` | Current request when present | Server-side authorization decision. Also emit an unsampled security audit record. |
| `tokennexus.feedback.submit` | `INTERNAL` | Feedback request span | Rating submission correlated to the original request by a span link when it occurs later. |

`tokennexus.request` is the trace's product root, but it can be a child of an
HTTP server span. Do not force every attempt into a child relationship when work
is queued, resumed, retried asynchronously, or executed by fan-out/fan-in. In those
cases, propagate the request context where valid and add a span link from the new
consumer or attempt span to the scheduling or prior-attempt span. Add link
attributes such as `tokennexus.link.type=escalation_from` and
`tokennexus.attempt.number=2`. Links and any sampler-relevant attributes must be
provided when the span is created.

If Microsoft Agent Framework Workflows is adopted, retain its native
`workflow.run` or `workflow.session`, `executor.process {executor_id}`,
`message.send`, and `edge_group.process` spans. Its link from target executor work
to the source `message.send` span already models asynchronous causality. Add only
TokenNexus product spans or attributes that are missing; do not recreate the
workflow graph as a second parallel trace tree.

### Span Attributes

All spans inherit standard resource attributes such as `service.name`,
`service.version`, `service.namespace`, `deployment.environment.name`, and the
cloud resource attributes supplied by the Azure Monitor distribution. Avoid
putting environment or service name on every span.

Use the installed GenAI semantic-convention package as the source of truth. The
MVP fields below match the current convention vocabulary, but GenAI conventions
remain subject to maturity and compatibility changes. Pin and record the package
version, then test the exported shape during every upgrade.

| Namespace | Attribute | Location | Cardinality and content rule |
| ----------- | ----------- | ---------- | ------------------------------ |
| Standard | `error.type` | Any failed span | Low-cardinality exception or stable error class; set span status to `ERROR` for failed operations. |
| GenAI | `gen_ai.operation.name` | Model or agent span | Convention value such as `chat`, `invoke_agent`, or `execute_tool`. |
| GenAI | `gen_ai.provider.name` | Model or agent span | Provider name, not deployment endpoint or account identifier. |
| GenAI | `gen_ai.request.model` | Model span | Configured model alias or model name. Prefer a stable alias for dashboards. |
| GenAI | `gen_ai.response.model` | Model span | Actual provider-returned model when available. |
| GenAI | `gen_ai.response.id` | Model span | Trace-only response identifier; never a metric dimension. |
| GenAI | `gen_ai.usage.input_tokens` | Completed model span | Provider count when available; otherwise omit and identify estimate source separately. |
| GenAI | `gen_ai.usage.output_tokens` | Completed model span | Provider count when available. |
| GenAI | `gen_ai.agent.id` and `gen_ai.agent.name` | Agent span | Stable configured identifiers; do not use user-generated names. |
| GenAI | `gen_ai.tool.name` and `gen_ai.tool.type` | Tool span | Allowlisted product tool and stable type only. |
| TokenNexus | `tokennexus.request.id` | Product spans and correlated logs | Opaque request ID. Never use on metrics or baggage. |
| TokenNexus | `tokennexus.application.id` | Request and policy spans | Controlled application or use-case alias. |
| TokenNexus | `tokennexus.policy.version` | Request, policy, escalation, and protected-action spans | Immutable version, bounded cardinality within a deployment window. |
| TokenNexus | `tokennexus.policy.action` | Policy span | Enum: `allow`, `downgrade`, `block`, or `approval_required`. |
| TokenNexus | `tokennexus.reason.codes` | Decision spans | Bounded array from one public allowlist. Never free-form explanations. |
| TokenNexus | `tokennexus.model.tier` | Policy and attempt spans | Enum such as `routine` or `frontier`; no provider secrets. |
| TokenNexus | `tokennexus.attempt.id` and `.number` | Attempt and evaluator spans | Trace-only opaque ID and integer 1 or 2. |
| TokenNexus | `tokennexus.cost.estimated_usd` | Policy, attempt, and request spans | Decimal-compatible numeric estimate with separately versioned price source. |
| TokenNexus | `tokennexus.pricing.version` | Policy and request spans | Immutable pricing configuration version. |
| TokenNexus | `tokennexus.token.input_estimated` | Policy span | Pre-execution estimate, distinct from provider usage. |
| TokenNexus | `tokennexus.token.avoided_estimated` | Cache and request spans | Estimated avoided tokens for accepted cache hits. |
| TokenNexus | `tokennexus.cache.outcome` | Cache span | Enum: `hit`, `miss`, or `bypass`. |
| TokenNexus | `tokennexus.cache.bypass_reason` | Cache span | Stable allowlisted reason; omit cache key, query, embedding, and response. |
| TokenNexus | `tokennexus.cache.entry_age_s` | Cache span | Numeric age only when an entry was considered. |
| TokenNexus | `tokennexus.quality.status` | Evaluator and request spans | Enum: `passed`, `below_threshold`, `unavailable`, or `not_applicable`. |
| TokenNexus | `tokennexus.quality.score` and `.threshold` | Evaluator span | Bounded numeric values; do not use scores as metric labels. |
| TokenNexus | `tokennexus.evaluator.version` | Evaluator span | Immutable evaluator and rubric version. |
| TokenNexus | `tokennexus.escalation.outcome` | Escalation and request spans | Enum: `not_needed`, `attempted`, `forbidden`, or `unavailable`. |
| TokenNexus | `tokennexus.tool.bounded_path` | Tool span | Boolean indicating the configured path and argument checks passed. |
| TokenNexus | `tokennexus.authz.decision` | Protected-action span | Enum: `allow` or `deny`. Do not include subject ID or token claims. |
| TokenNexus | `tokennexus.dependency.status` | Dependency span | Enum: `ok`, `timeout`, `error`, `unavailable`, or `degraded`. |
| TokenNexus | `tokennexus.evaluation.manifest_version` | Request span in evaluation runs | Immutable evaluation set version; bounded and absent from normal traffic. |

Use OpenTelemetry SDK limits as a safety net, not a design target. Configure and
test explicit limits of at most 128 attributes, 128 events, and 128 links per span,
and at most 128 attributes per event or link. Set an attribute-value length limit
appropriate to the backend, for example 1,024 characters, after confirming SDK
support. The proposed schema should normally use fewer than 40 attributes per
span. Export SDK self-diagnostics or counters for dropped spans, logs, metric
points, attributes, events, links, and export failures.

### Events and Logs

Map the PRD instrumentation events to span events on `tokennexus.request` when
they mark a meaningful instant rather than a timed operation:

| Event | Recommended representation |
| ------- | ---------------------------- |
| `request_received` | Request-span start attributes. Emit an event only when acceptance occurs after a material validation phase. |
| `policy_decided` | End state of `tokennexus.policy.evaluate`; optionally add a request event with action and reason codes for a concise timeline. |
| `cache_evaluated` | End state of `tokennexus.cache.lookup`; add a request event only for a hit or privacy bypass. |
| `model_attempt_completed` | End state and duration of the GenAI client span; do not duplicate token data in a log by default. |
| `quality_evaluated` | End state of `tokennexus.quality.evaluate`; add a request event when below threshold or unavailable. |
| `request_completed` | Request-span end attributes and status. The durable execution record remains authoritative. |
| `protected_action_attempted` | Span plus a structured, unsampled security audit log or dedicated audit sink. |
| `feedback_submitted` | Feedback span and durable feedback record; link to the original request trace when its context is retained. |

Application logs must be structured and automatically correlated with active
`trace_id` and `span_id`. Log records should use a stable `event.name`, severity,
component, status, public reason codes, and request ID where operationally needed.
Message bodies must be fixed templates, not interpolated prompts, responses,
arguments, cache values, authorization tokens, or exception payloads from remote
systems. Sanitize exception messages before export. Security audit records need
their own retention and access policy and must survive trace sampling.

### Metrics

Use standard GenAI metrics emitted by supported instrumentation, including
`gen_ai.client.operation.duration` and `gen_ai.client.token.usage`. Do not create
duplicates with slightly different names. Add the following product metrics only
where standard metrics do not express the requirement:

| Metric | Instrument and unit | Allowed dimensions |
| -------- | --------------------- | -------------------- |
| `tokennexus.request.duration` | Histogram, seconds | `status`, `cache.outcome`, `escalation.outcome`, `application.id`, `deployment.environment.name` |
| `tokennexus.orchestration.duration` | Histogram, seconds | `status`, `application.id` |
| `tokennexus.request.cost.estimated` | Histogram, USD | `model.tier`, `provider.name`, `cache.outcome`, `application.id` |
| `tokennexus.request.cost.baseline_estimated` | Histogram, USD | `application.id`, `evaluation.manifest_version` in controlled evaluation only |
| `tokennexus.request.count` | Counter, requests | `status`, `policy.action`, `cache.outcome`, `escalation.outcome`, `application.id` |
| `tokennexus.cache.lookup.count` | Counter, lookups | `outcome`, `bypass_reason`, `application.id` |
| `tokennexus.cache.token_avoided` | Counter, tokens | `application.id`, `model.tier` |
| `tokennexus.quality.score` | Histogram, score unit | `status`, `evaluator.version`, `application.id`, `model.tier` |
| `tokennexus.budget.action.count` | Counter, actions | `action`, `reason_code`, `application.id` |
| `tokennexus.escalation.count` | Counter, escalations | `outcome`, `reason_code`, `application.id` |
| `tokennexus.tool.invocation.count` | Counter, calls | `tool.name`, `status`, `authz.decision` |
| `tokennexus.dependency.duration` | Histogram, seconds | `dependency.type`, `status` |
| `tokennexus.telemetry.export.failure` | Counter, failures | `signal`, `exporter`, `reason_class` |

Keep each dimension on a controlled vocabulary and enforce a cardinality budget
in tests. Never dimension metrics by request ID, trace ID, span ID, attempt ID,
response ID, user or tenant ID, session ID, raw model response, reason text, URL,
cache key, or exception message. Metrics are not trace-sampled, so use them for
service-level rates and p95 objectives even when production traces are sampled.

### Propagation and Baggage

Propagate W3C `traceparent` and `tracestate` across HTTP, queues, and locally
opened MCP sessions using the framework's propagator. For scheduled or queued work,
extract the producer context, create the consumer span with the appropriate remote
parent when it represents continuation, and use links for batch, retry, fan-in, or
other non-nested causality.

The TokenNexus baggage allowlist should initially contain only:

* `tokennexus.application.id`
* `tokennexus.request.class` as a controlled routine, complex, or critical enum
* `tokennexus.evaluation.cohort` only in non-production evaluation traffic

Do not put request ID, user ID, tenant ID, policy text, prompt classification,
budget, quality score, cache key, authorization context, role, or sampling priority
in baggage. Copy allowlisted baggage to selected spans through an explicit
processor; baggage is not exported automatically as span attributes. Enforce a
TokenNexus limit of three members, 256 bytes total, and 64 bytes per value, even
though the W3C propagation floor is 64 members and 8,192 bytes. Clear all baggage
at outbound public, model-provider, third-party-tool, and cross-tenant trust
boundaries unless a reviewed contract requires a specific member.

### Privacy, Redaction, and Security

Production uses metadata-only telemetry. Microsoft Agent Framework instrumentation
is enabled, but `ENABLE_SENSITIVE_DATA=false` and equivalent SDK content-capture
switches remain off. This excludes prompts, responses, tool arguments, tool
results, executor inputs and outputs, and workflow message content. Instrument
either the agent or chat client when both would duplicate content or spans.

Apply a centralized telemetry policy before export:

1. Allowlist attributes and event fields by span type and schema version.
2. Drop unknown attributes under content-bearing namespaces.
3. Remove secrets, credentials, tokens, personal identifiers, raw URLs and query
   strings, prompt or response text, embeddings, cache values, tool arguments and
   results, hidden instructions, and free-form feedback.
4. Normalize exception data to `error.type`, a stable reason code, and a sanitized
   message when a message is necessary.
5. Hash an identifier only when correlation is essential and privacy approval
   covers linkability; prefer omission or a short-lived opaque surrogate.
6. Clear baggage and optionally restart trace context at defined trust boundaries.
7. Restrict telemetry access, retention, export destinations, and diagnostic
   content capture by environment.

Content capture for a controlled development investigation must require an
explicit, time-bounded change, isolated telemetry destination, restricted access,
short retention, documented approval, and an automatic return to off. Redaction
after collection is not an adequate default because SDK, queue, exporter, and
backend stages may already have received the content.

Do not trust an inbound sampled flag to force unlimited collection on a public
endpoint. Apply local rate, authentication, and sampling controls to prevent a
caller from increasing telemetry cost or creating denial-of-service pressure.

### Sampling and Completeness

Use the following staged policy:

| Traffic | Trace policy | Rationale |
| --------- | -------------- | ----------- |
| MVP acceptance and 30-request paired evaluation | 100% recording and export in an isolated, access-controlled environment | FR-009 and FR-010 require complete, inspectable evidence. |
| Security negative tests | 100% traces plus independent audit records | A sampled trace cannot be the only FR-016 or FR-020 evidence. |
| Local deterministic tests | In-memory exporters with always-on sampling | Exact span, link, event, and redaction assertions. |
| Initial production | Parent-based, ratio-based head sampling with a documented starting ratio and ingestion budget | Simple, predictable, and no stateful Collector dependency. |
| Production aggregates | Unsampled metrics and independent audit logs | Preserve SLO, budget, authorization, and telemetry-health evidence. |

Because head sampling occurs at span creation, later error, latency, quality, or
escalation outcomes cannot retroactively retain a dropped trace. Emit unsampled
aggregate metrics and correlated error or audit logs, and provide a temporary,
access-controlled diagnostic sampling override for incident response. Do not add
tail sampling to the MVP. If later evidence shows a need to retain all errors or
slow traces, introduce an OpenTelemetry Collector tail-sampling tier only after
load tests establish memory, decision wait, dropped-trace behavior, and trace-ID
affinity across Collector replicas.

### Evidence and Dashboards

Application Insights should support these initial views:

* Request volume, success and controlled-outcome rate, p50 and p95 end-to-end
  latency, and p95 orchestration overhead.
* Cost and token usage by application, stable model tier, provider, cache outcome,
  and escalation outcome.
* Cache hit, miss, privacy bypass, freshness bypass, avoided tokens, and estimated
  savings.
* Quality-score distribution, below-threshold rate, evaluator unavailable rate,
  escalation attempted or forbidden rate, and final status.
* Provider, evaluator, cache, tool, and telemetry dependency latency and failure.
* Budget allow, downgrade, block, and approval-required actions by public reason.
* Telemetry export failures, queue pressure, dropped data, and completeness-test
  results.

Use Application Insights end-to-end transactions for individual traces and KQL
or Azure Monitor Grafana dashboards for TokenNexus-specific economics and controls.
Application Insights maps OpenTelemetry internal or client spans to dependencies,
server or consumer spans to requests, and custom span attributes to
`customDimensions`; validate these mappings against the deployed SDK version.

Every compliance artifact should include an evidence manifest with control ID,
test-run ID, evaluation manifest version, telemetry query version, time window,
environment, expected count, observed count, and artifact URI. The URI must point
to the controlled evidence store rather than embedding evidence bodies in
telemetry.

## Alternatives

| Pattern | Advantages | Costs and risks | Decision |
| --------- | ------------ | ----------------- | ---------- |
| Azure Monitor OpenTelemetry distribution exporting directly to Application Insights | Fewest moving parts, Microsoft-supported Azure integration, automatic resource and common-library instrumentation, and immediate end-to-end transaction views | Backend-specific configuration remains in the application environment; limited central processing; schema changes must be handled in application processors | Recommended for the MVP. Configure providers once per process and use batch processors outside tests. |
| OTLP from applications to an OpenTelemetry Collector, then Azure Monitor | Vendor-neutral application endpoint, centralized filtering, batching, routing, retries, and future tail sampling | Adds an availability tier, queues, memory, security, upgrades, and exporter compatibility risk; tail sampling requires all spans for a trace to reach the same sampling decision point | Adopt after the MVP when multiple services, exporters, centralized policy, or tail sampling justify the operating cost. |
| Dual export from each application to Application Insights and an OTLP backend | Fast Azure experience plus a second analysis or migration path | Duplicate cost and data exposure, inconsistent success, more exporter backpressure, and confusing duplicate views if both paths feed the same backend | Use only for a time-bounded migration or compatibility test. Never send both paths into the same Application Insights resource. |
| Logs or a custom execution table without traces | Simple durable reporting and easy business-schema control | Loses distributed timing, parent-child causality, framework integration, and end-to-end diagnostics | Retain the durable execution table, but correlate it with OpenTelemetry rather than replacing traces. |

## MVP Recommendation

Use the Azure Monitor OpenTelemetry distribution in each TokenNexus service and
export traces, metrics, and structured logs directly to one environment-specific
Application Insights resource. Configure one OpenTelemetry provider set per
process with batch export, W3C propagation, explicit SDK limits, metadata-only
Agent Framework instrumentation, and a TokenNexus allowlist processor.

Implement one `tokennexus.request` span around the accepted business request.
Create child policy, cache, evaluator, escalation, authorization, and product-tool
spans; use existing framework or provider GenAI client spans for model calls. Use
links for asynchronous retries, escalation attempts, feedback, and workflow
messages when parentage would falsely imply nested execution. Put the request ID
on spans and structured logs, but keep the independently validated execution
record authoritative.

Run acceptance, security, and paired baseline evaluations with always-on sampling
in an isolated environment. Start production with parent-based ratio head sampling,
unsampled low-cardinality metrics, and an independent authorization audit path.
Do not deploy a Collector or tail sampling until measurements demonstrate the
need.

The implementation sequence is:

1. Publish telemetry schema version `1.0.0`, enumerations, and the public reason-code
   registry.
2. Configure resource identity, Azure Monitor exporters, batch processors,
   propagation, limits, redaction, and telemetry self-diagnostics.
3. Instrument the request, policy, cache, evaluator, escalation, protected-action,
   feedback, and bounded-tool boundaries without duplicating framework spans.
4. Map the durable execution record to trace and span IDs and validate it separately.
5. Add standard GenAI and proposed TokenNexus metrics with cardinality tests.
6. Build Application Insights queries and versioned evidence manifests for goals
   and CR-001 through CR-008.
7. Run deterministic telemetry contract, leakage, failure, and backend mapping tests
   before production traffic.

### Validation Plan

| Test | Method | Pass condition |
| ------ | -------- | ---------------- |
| Complete successful request | Deterministic model, evaluator, cache, and price adapters with in-memory trace, metric, and log exporters | Exactly one request span contains policy and final outcome; required child operations, IDs, token counts, and duration values correlate with one execution record. |
| Cache hit and bypass | Seed deterministic cache outcomes | Hit has no model span and records avoided tokens; sensitive and freshness cases bypass without cache keys or content. |
| One-step escalation | Seed a below-threshold first response and passing second response | Two attempt spans share the request, attempt 2 is linked or parented correctly, and no third attempt exists. |
| Controlled non-escalation | Deny by budget, latency, and policy in separate fixtures | No second attempt occurs; public reason codes match the durable record and contain no policy internals. |
| Dependency degradation | Inject provider, evaluator, cache, and exporter timeouts | Request behavior matches NFR-004; dependency status and unsampled failure metrics remain available without secrets. |
| Trace propagation | Exercise HTTP, queue, and locally opened MCP paths | Trace context continues where allowed; async causality uses links; baggage contains only the allowlist and is cleared at trust boundaries. |
| Sensitive-data leakage | Seed canary API keys, personal data, hidden instructions, prompt text, response text, tool arguments, tool results, URLs, and exception payloads | No canary appears in exported spans, events, logs, metrics, baggage, exporter diagnostics, or Application Insights fields. |
| Content-capture default | Start with production configuration | Sensitive capture is false, message events containing content are absent, and startup fails validation if a prohibited switch is enabled. |
| Cardinality | Generate unique request, user, response, cache, and exception values | Metric time-series dimensions remain within the approved vocabulary and contain none of the unique values. |
| SDK limits | Generate excess attributes, events, links, and long values | Request still completes; truncation or drops are observable in SDK diagnostics; required fields survive priority rules. |
| Sampling | Run identical fixtures under always-on and production samplers | Evaluation is complete under always-on; aggregate metrics and audit evidence remain correct when request traces are sampled out. |
| Export failure | Reject or interrupt the Azure exporter | Product request has a bounded unaffected or degraded outcome; exporter failure is locally observable and queues remain bounded. |
| Azure backend mapping | Send a known fixture to the release Application Insights resource | Requests, dependencies, trace correlation, `customDimensions`, GenAI views, and metric units match the contract. |
| Schema compatibility | Pin a golden OTLP representation and upgrade one dependency at a time | GenAI field names, types, span names, and custom schema stay compatible or produce an approved migration. |

Tests must not call paid model, evaluator, embedding, cache, pricing, or tool
services unless explicitly marked integration tests. Use deterministic substitutes,
a fixed clock, fixed IDs where supported, an in-memory span exporter, an in-memory
metric reader, and a capturing log exporter. Repeat the evaluation twice and
compare policy and telemetry outcomes as required by NFR-007.

## Gaps and Clarifying Questions

The following decisions cannot be settled from the PRD alone:

* The implementation language and exact Agent Framework, OpenTelemetry SDK, GenAI
  semantic-convention, and Azure Monitor distribution versions are not selected.
  Exported field names and processor capabilities must be validated after selection.
* Application Insights workspace, region, retention, daily cap, RBAC, private-link,
  and data-residency requirements need accountable platform, privacy, and security
  owners.
* The production trace sampling ratio needs a traffic and ingestion-cost forecast.
* Stable model aliases, application IDs, tool names, dependency types, status enums,
  and public reason codes need a governed registry and cardinality budgets.
* Estimated cost precision, currency handling, token-estimate provenance, and
  reconciliation with provider billing need FinOps approval.
* The quality score range, aggregation rules, evaluator version format, and treatment
  of evaluator unavailability need product approval.
* Audit-log destination, immutability, retention, access, and incident workflow need
  security approval. Application traces alone are insufficient audit evidence.
* Trace-context and baggage behavior for hosted or provider-managed MCP tools needs
  an integration test because local Agent Framework injection does not control that
  hosted boundary.
* The evidence store and URI format for CR-001 through CR-008 are not specified.
* Requirements for temporary diagnostic content capture may be prohibited entirely;
  privacy and legal owners must decide before such a path is implemented.

Recommended next research:

* Select the implementation stack and verify exact emitted OTLP with a minimal
  instrumented request.
* Test GenAI Agent details and custom-dimension mappings in the intended Application
  Insights resource.
* Model expected telemetry volume and cost to set production sampling, retention,
  and daily caps.
* Define the governed telemetry schema registry, reason-code registry, and migration
  policy.
* Threat-model telemetry ingestion, baggage boundaries, exporter credentials,
  content-capture controls, and audit storage.
* Prototype the KQL and Grafana queries needed for each goal and compliance control.

## References

* [OpenTelemetry trace API](https://opentelemetry.io/docs/specs/otel/trace/api/)
* [OpenTelemetry trace SDK](https://opentelemetry.io/docs/specs/otel/trace/sdk/)
* [OpenTelemetry general SDK configuration](https://opentelemetry.io/docs/specs/otel/configuration/sdk/)
* [OpenTelemetry semantic conventions for generative AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)
* [OpenTelemetry GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
* [OpenTelemetry GenAI metrics](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-metrics/)
* [OpenTelemetry attribute naming](https://opentelemetry.io/docs/specs/semconv/general/attribute-naming/)
* [OpenTelemetry logs data model](https://opentelemetry.io/docs/specs/otel/logs/data-model/)
* [OpenTelemetry baggage API](https://opentelemetry.io/docs/specs/otel/baggage/api/)
* [OpenTelemetry Collector architecture](https://opentelemetry.io/docs/collector/architecture/)
* [OpenTelemetry Collector tail sampling](https://opentelemetry.io/docs/collector/transforming-telemetry/)
* [W3C Trace Context](https://www.w3.org/TR/trace-context/)
* [W3C Baggage](https://www.w3.org/TR/baggage/)
* [Microsoft Agent Framework agent observability](https://learn.microsoft.com/agent-framework/agents/observability)
* [Microsoft Agent Framework workflow observability](https://learn.microsoft.com/agent-framework/workflows/observability)
* [Azure Monitor OpenTelemetry overview](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-overview)
* [Enable Azure Monitor OpenTelemetry](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-enable)
* [Configure Azure Monitor OpenTelemetry](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-configuration)
* [Customize Azure Monitor OpenTelemetry](https://learn.microsoft.com/azure/azure-monitor/app/opentelemetry-add-modify)
* [Application Insights sampling](https://learn.microsoft.com/azure/azure-monitor/app/sampling-classic-api)
* [Application Insights distributed tracing](https://learn.microsoft.com/azure/azure-monitor/app/distributed-trace-data)
* [Monitor AI agents with Application Insights](https://learn.microsoft.com/azure/azure-monitor/app/agents-view)
