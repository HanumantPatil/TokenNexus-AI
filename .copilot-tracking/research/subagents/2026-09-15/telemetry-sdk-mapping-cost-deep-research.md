---
title: Telemetry SDK Mapping and Cost Deep Research
description: Concrete language-neutral observability choices with Python and .NET implementation notes for TokenNexus-AI-Framework
author: GitHub Copilot
ms.date: 2026-09-15
ms.topic: concept
---

## Research Scope

* Verify current Azure Monitor OpenTelemetry distributions for likely Python and .NET stacks without selecting a language
* Research Microsoft Agent Framework instrumentation and OpenTelemetry Generative AI semantic-convention maturity and opt-in behavior
* Map spans, logs, attributes, sampling, retention, daily caps, RBAC, and ingestion cost to Application Insights
* Define telemetry schema migration, KQL evidence queries, and golden OTLP contract tests
* Identify claims that require a live Application Insights backend integration test
* Recommend one language-neutral observability contract with stack-specific implementation notes

## Source Documents

* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/opentelemetry-agent-observability-research.md
* docs/prds/tokennexus-ai-framework-prd.md

## Status

Complete. The selected pattern is language-neutral and keeps Python and .NET as
implementation options. Package behavior, Azure table mappings, security controls,
cost estimation, migration rules, KQL evidence, and contract tests are specified.
Claims that still require a live backend test are identified separately.

## Findings

### Selected Pattern

Use one versioned TokenNexus telemetry contract over OpenTelemetry, implemented
with Microsoft Agent Framework instrumentation and the Azure Monitor
OpenTelemetry distribution. Export directly to one workspace-based Application
Insights resource per environment for the MVP. Keep the durable execution record
and security audit sink authoritative because traces and correlated logs can be
sampled, capped, delayed, or dropped.

The contract has four layers:

1. Retain native HTTP, Agent Framework, workflow, and GenAI spans without
     recreating them.
2. Add TokenNexus spans and `tokennexus.*` attributes only for product decisions
     absent from native instrumentation.
3. Normalize Python and .NET telemetry into one semantic assertion model for
     tests and KQL. Do not require identical raw span names across runtimes.
4. Pin all telemetry dependencies and semantic-convention mode, record them in
     an evidence manifest, and run golden OTLP plus live Application Insights tests
     before any upgrade.

Direct export is preferred over an OpenTelemetry Collector for the MVP because
one service and one destination do not yet justify another stateful availability
and security boundary. Add a Collector when multiple services, destinations,
central redaction, or tail sampling provide measured value.

### Contract Invariants

The language-neutral contract uses instrumentation scope
`TokenNexus.Observability` and resource attribute
`tokennexus.telemetry.schema.version=1.0.0`. Every accepted request has one
`tokennexus.request` product-root span below the transport span and the following
queryable metadata where applicable:

* `tokennexus.request.id`
* `tokennexus.application.id`
* `tokennexus.policy.version`
* `tokennexus.policy.action`
* `tokennexus.reason.codes`
* `tokennexus.model.tier`
* `tokennexus.attempt.number`
* `tokennexus.cost.estimated_usd`
* `tokennexus.pricing.version`
* `tokennexus.cache.outcome`
* `tokennexus.quality.status`
* `tokennexus.evaluator.version`
* `tokennexus.escalation.outcome`
* `tokennexus.final.status`

Use only allowlisted enums and opaque identifiers. Never use request, trace,
attempt, response, user, tenant, session, or cache-entry identifiers as metric
dimensions. Raw prompts, responses, tool definitions, arguments, results,
embeddings, credentials, URLs with query strings, and free-form feedback are
prohibited in production telemetry.

Required timed operations remain:

* `tokennexus.policy.evaluate`
* `tokennexus.cache.lookup`
* One native GenAI model span per paid attempt
* `tokennexus.quality.evaluate`
* `tokennexus.escalation.evaluate`
* `tokennexus.orchestration`
* Native or TokenNexus bounded-tool spans without duplication

Metrics remain unsampled and use low-cardinality dimensions. At minimum emit
`tokennexus.request.count`, `tokennexus.request.duration`,
`tokennexus.orchestration.duration`, `tokennexus.request.cost.estimated`,
`tokennexus.cache.lookup.count`, `tokennexus.quality.score`, and
`tokennexus.escalation.count`. Use the standard
`gen_ai.client.operation.duration` and `gen_ai.client.token.usage` metrics when
the selected Agent Framework version emits them.

### Stack-Specific Implementation Notes

#### Python

* Use the `azure-monitor-opentelemetry` distribution, whose public setup entry
    point is `configure_azure_monitor()`.
* Agent Framework installs the OpenTelemetry API, SDK, and AI semantic-convention
    package, but no exporter. Configure Azure Monitor once at process startup, pass
    `create_resource()`, then call `enable_instrumentation()` with sensitive data
    disabled.
* A plain Agent Framework `Agent` already includes its telemetry layer. Avoid a
    second wrapper that emits duplicate agent and chat spans.
* Explicitly set and test the semantic-convention mode. Current Agent Framework
    behavior uses latest experimental conventions when
    `OTEL_SEMCONV_STABILITY_OPT_IN` is unset. A set value that omits the
    case-sensitive `gen_ai_latest_experimental` token selects its v1.36
    compatibility behavior. Freeze one mode in deployment configuration rather
    than accepting this implicit default.
* Keep `ENABLE_SENSITIVE_DATA=false`. `ENABLE_MESSAGE_EVENTS` does not expose
    message events unless instrumentation and sensitive data are also enabled, but
    set it false in production for defense in depth.
* Use `logger_name` to constrain Python logging export and avoid collecting the
    Azure SDK's own logs through the same logger tree.
* Starting with Azure Monitor Python distribution 1.8.6, rate-limited sampling
    is the default. Override it explicitly so evaluation and production behavior
    cannot change with a distribution update.
* Agent Framework automatically propagates W3C context to MCP sessions opened by
    the process. Hosted or provider-managed MCP calls are outside this mechanism
    and require an integration test.

#### .NET

* For ASP.NET Core, prefer `Azure.Monitor.OpenTelemetry.AspNetCore` and
    `AddOpenTelemetry().UseAzureMonitor()`. For a console or worker service, use
    `Azure.Monitor.OpenTelemetry.Exporter` and attach trace, metric, and log
    exporters to providers that live for the full process lifetime.
* Match Agent Framework's `.UseOpenTelemetry(sourceName: ...)` source with
    `.AddSource(...)`. The framework default source is
    `Experimental.Microsoft.Agents.AI`; use a product-owned stable source name and
    test it to avoid silent span loss.
* Configure OpenTelemetry on either the agent or the chat-client layer unless
    duplication is intentional. Agent Framework warns that instrumenting both can
    duplicate chat context and spans.
* Keep `EnableSensitiveData=false` and
    `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT` unset or false.
* Use `IncludeFormattedMessage` only for allowlisted fixed templates. Enable
    scopes only after verifying that no user content or authorization context is
    copied into log attributes.
* Azure Monitor uses `ApplicationInsightsSampler` when the distribution is not
    configured. Set the production strategy explicitly.
* Agent Framework workflow telemetry differs from Python. Current .NET workflow
    names include `workflow.session` and `workflow_invoke`; Python uses
    `workflow.run`. Normalize these to `workflow.run` in contract assertions rather
    than renaming native spans.

### GenAI Semantic-Convention Stability

The former OpenTelemetry website pages now state that GenAI conventions moved to
the standalone `open-telemetry/semantic-conventions-genai` repository. As of this
research date, that repository has no published releases and its schema URL is
still marked `TODO`. Active changes include agent, inference, evaluation, MCP,
and content attributes. Treat this surface as experimental even when an SDK
provides a compatibility profile.

TokenNexus should therefore depend on a deliberately small GenAI subset:

* `gen_ai.operation.name`
* `gen_ai.provider.name` or the pinned compatibility equivalent
* `gen_ai.request.model`
* `gen_ai.response.model`
* `gen_ai.response.id`
* `gen_ai.usage.input_tokens`
* `gen_ai.usage.output_tokens`
* `gen_ai.agent.id`
* `gen_ai.agent.name`
* `gen_ai.tool.name`

Do not make policy, evidence, cost, or authorization logic depend on those fields.
Normalize provider naming differences such as `gen_ai.system` versus
`gen_ai.provider.name` in the evidence view. Record the Agent Framework version,
OpenTelemetry SDK version, Azure distribution version, semantic-convention
package version or commit, and selected mode with each golden fixture.

### Application Insights Mapping

Use Log Analytics workspace table names in all new queries. Application Insights
uses different compatibility names in its resource-scoped Logs experience.

| OpenTelemetry data | Workspace destination | Important fields |
| ------------------ | --------------------- | ---------------- |
| Server and consumer spans | `AppRequests` | `Id`, `OperationId`, `ParentId`, `Name`, `DurationMs`, `Success`, `ResultCode`, `Properties`, `Measurements`, `ItemCount` |
| Client and internal spans | `AppDependencies` | `Id`, `OperationId`, `ParentId`, `Name`, `DependencyType`, `Target`, `DurationMs`, `Success`, `ResultCode`, `Properties`, `Measurements`, `ItemCount` |
| Application log records | `AppTraces` | `OperationId`, `ParentId`, `Message`, `SeverityLevel`, `Properties`, `Measurements`, `ItemCount` |
| Exceptions | `AppExceptions` | `OperationId`, `ParentId`, exception fields, `Properties`, `Measurements`, `ItemCount` |
| OpenTelemetry metrics | `AppMetrics` | `Name`, `Sum`, `Min`, `Max`, `ItemCount`, `Properties` |
| GenAI content attributes | `AppGenAIContent` | Content-bearing values and references to source telemetry |

Custom span and log attributes normally appear in dynamic `Properties`; numeric
custom measurements appear in `Measurements`. Azure documents maximum custom
property key and value lengths of 150 and 8,192 characters, respectively. The
TokenNexus 1,024-character value limit remains the safer contract.

Application Insights stores log records in `AppTraces`; OpenTelemetry spans are
not stored there. Azure maps spans to `AppRequests` or `AppDependencies` based on
span kind. Validate the exact mapping of Agent Framework internal and client spans
because this behavior is exporter and version dependent.

Starting September 30, 2026, Application Insights will stop storing the values of
seven GenAI content attributes in `AppDependencies`, `AppTraces`, and `AppEvents`.
The keys remain, but values become pointers to `AppGenAIContent`. The affected
attributes include input and output messages, system instructions, tool
definitions, tool-call arguments and results, and evaluation explanations.
TokenNexus production policy prohibits these values, but any controlled diagnostic
query or canary must support `AppGenAIContent`. Early migration uses the
`protectGenAISensitiveData` preview feature; the temporary opt-out ends on
September 30, 2027.

### Sampling Configuration

Use Azure Monitor's custom sampler, not a generic sampler, to preserve Azure trace
cohesion and Live Metrics compatibility. Make its behavior explicit in every
environment:

| Environment | Strategy | Initial setting |
| ----------- | -------- | --------------- |
| Unit and golden-contract tests | Always on through in-memory or capturing exporters | 100% |
| Acceptance, security, and 30-request evaluation | Azure fixed percentage | `1.0` |
| Initial low-volume production | Azure fixed percentage | `1.0`, then reduce only after measuring ingestion |
| Higher-volume production | Azure fixed percentage | Start trial at `0.05`, then calibrate from evidence |

Azure's current documentation suggests 5% only as a starting point when fixed
percentage is required. It is not a TokenNexus production default. Prefer fixed
percentage over rate limiting for cross-replica comparability and paired evidence,
then confirm trace integrity across every service. Metrics are never sampled.

Enable trace-based log sampling so logs within an unsampled trace follow its
decision. Keep security audit records and durable execution records on independent,
unsampled paths. Any KQL count over sampled trace tables must use `sum(ItemCount)`
for estimated population counts, while completeness tests must run at 100% and use
physical record counts.

Daily caps are emergency brakes, not a routine control. They can overshoot, still
bill excess data, and make monitoring blind until the workspace-specific reset
hour. Alert before the cap and on `_LogOperation` records containing `OverQuota`.

### Retention, Caps, and RBAC

Use a workspace-based Application Insights resource and set retention by table.
Current Azure documentation gives Application Insights tables 90 days of included
retention. General workspace tables default to 30 days, Analytics tables support
4 to 730 days of interactive retention, and total retention can extend to 4,383
days. Lowering Analytics retention below the included period does not reduce
ingestion cost.

Recommended governance baseline:

* Keep metadata-only `AppRequests`, `AppDependencies`, `AppTraces`, `AppMetrics`,
    and `AppExceptions` for 90 days until operational and compliance owners approve
    a different value.
* Set `AppGenAIContent` to `Protected` before any controlled content test. Use the
    shortest approved retention and keep content capture disabled in production.
* Assign `Log Analytics Data Reader` with granular RBAC conditions for query-only
    personas. Avoid broad `Reader`, `Monitoring Reader`, and contributor roles when
    table or row restrictions are required because RBAC is additive.
* Use workspace-level scope, security groups, and managed identities for alerts.
    Audit conditional queries through `LAQueryLogs.ConditionalDataAccess`.
* Treat protected tables and `DataActionsOnly` as preview-dependent controls until
    the target subscription validates availability and operating behavior.
* Keep telemetry configuration roles separate from data-reader roles. Daily-cap
    and retention changes require contributor-level workspace permissions.

Resource-context access is useful for application teams, but granular ABAC has
important access-mode prerequisites. Validate the effective role graph, including
inherited assignments, because any broader assignment can override intended
conditions.

### Ingestion-Cost Estimation

Do not estimate Azure Monitor cost from OTLP payload bytes. Azure bills the string
representation of stored columns in decimal GB and excludes standard columns from
the calculation. The authoritative observed quantity is `_BilledSize` where
`_IsBillable` is true.

Use a 7-to-14-day representative run with production-like sampling and traffic:

```kusto
union withsource=TableName
        AppRequests,
        AppDependencies,
        AppTraces,
        AppExceptions,
        AppEvents,
        AppMetrics,
        AppGenAIContent
| where TimeGenerated >= ago(14d)
| where _IsBillable =~ "true"
| summarize BillableGB=sum(_BilledSize) / 1e9 by TableName, bin(TimeGenerated, 1d)
| order by TimeGenerated asc, BillableGB desc
```

Calculate projected monthly ingestion as:

```text
mean representative billable GB/day * expected traffic multiplier * 30.4375
```

Multiply by the target region, currency, offer, and Analytics Logs price from the
Azure pricing calculator. Add extended retention, export, alert, and search costs
only when configured. Compare pay-as-you-go with commitment tiers only near the
100 GB/day entry point. Reconcile the estimate with Workspace **Usage and estimated
costs** and Azure Cost Management after deployment.

For pre-backend planning, serialize representative records through both runtime
exporters and apply a conservative range rather than a point estimate. Microsoft
states billed Analytics and Basic records average about 25% smaller than incoming
JSON, but can differ materially. Replace that assumption with `_BilledSize` as soon
as live data exists.

### Telemetry Schema Migration

Apply these rules to both TokenNexus and upstream telemetry:

1. Pin runtime, Agent Framework, OpenTelemetry, Azure distribution, and semantic-
     convention dependencies in the release manifest.
2. Treat additive optional `tokennexus.*` fields as minor schema changes. Treat a
     rename, type change, semantic change, required-field addition, or enum removal
     as a major change.
3. Never rename or repurpose a field in place. Dual emit old and new fields for one
     bounded migration window when privacy permits.
4. Publish versioned normalization functions or KQL functions that read both
     versions and produce one stable evidence view.
5. Run old-reader/new-writer and new-reader/old-writer golden tests.
6. Deploy dashboards and queries before writers when adding a new representation;
     retire old queries only after retention has aged out old records.
7. Test all upstream package upgrades against normalized semantics and raw
     exporter shape. Do not treat a package minor version as schema-safe.
8. Update content queries for `AppGenAIContent` before September 30, 2026, even if
     content capture is expected to remain disabled.

### KQL Evidence Queries

These examples target Log Analytics workspace tables. Run release evidence with
100% sampling and substitute the frozen time window, resource ID, schema version,
and evaluation manifest. Property names must be confirmed by the live mapping
test because exporter versions can sanitize dots or serialize arrays differently.

#### Telemetry Completeness

This query expects one product root plus policy, cache, orchestration, final
quality state, and any required attempt spans per completed request:

```kusto
let startTime = datetime(2026-09-15T00:00:00Z);
let endTime = datetime(2026-09-16T00:00:00Z);
let spans = union AppRequests, AppDependencies
| where TimeGenerated between (startTime .. endTime)
| extend RequestId=tostring(Properties["tokennexus.request.id"])
| where isnotempty(RequestId)
| project RequestId, Name, Properties, OperationId;
spans
| summarize
        Root=countif(Name == "tokennexus.request"),
        Policy=countif(Name == "tokennexus.policy.evaluate"),
        Cache=countif(Name == "tokennexus.cache.lookup"),
        Orchestration=countif(Name == "tokennexus.orchestration"),
        Quality=countif(Name == "tokennexus.quality.evaluate"),
        Attempts=countif(isnotempty(tostring(Properties["tokennexus.attempt.number"]))),
        FinalStatus=any(tostring(Properties["tokennexus.final.status"])),
        OperationIds=dcount(OperationId)
    by RequestId
| extend Complete=
        Root == 1 and Policy == 1 and Cache == 1 and Orchestration == 1
        and isnotempty(FinalStatus) and OperationIds == 1
| summarize CompletedRequests=count(), CompleteRequests=countif(Complete),
        CompletenessPct=100.0 * countif(Complete) / count()
```

Join the result to the durable execution-record manifest. A telemetry-only query
cannot prove that every expected request reached the backend when the entire trace
is missing.

#### One-Step Escalation

```kusto
union AppRequests, AppDependencies
| where TimeGenerated >= ago(24h)
| extend
        RequestId=tostring(Properties["tokennexus.request.id"]),
        Attempt=toint(Properties["tokennexus.attempt.number"]),
        Escalation=tostring(Properties["tokennexus.escalation.outcome"])
| where isnotempty(RequestId)
| summarize
        Attempts=make_set(Attempt),
        PaidAttemptSpans=countif(isnotnull(Attempt)),
        EscalationOutcomes=make_set(Escalation)
    by RequestId
| extend Pass=
        PaidAttemptSpans <= 2
        and array_index_of(Attempts, 3) == -1
        and (PaidAttemptSpans != 2 or array_index_of(Attempts, 2) >= 0)
| where not(Pass)
```

An empty result is the pass condition. Add an assertion that seeded low-quality
fixtures contain attempts 1 and 2 and one `attempted` escalation outcome.

#### Sensitive-Content Canary

Run a unique canary only in an isolated test environment. Search every potentially
content-bearing column and the dedicated GenAI table:

```kusto
let canary = "TNX-CANARY-REPLACE-WITH-UNIQUE-VALUE";
union isfuzzy=true withsource=TableName
        AppRequests,
        AppDependencies,
        AppTraces,
        AppExceptions,
        AppEvents,
        AppGenAIContent
| where TimeGenerated >= ago(2h)
| extend Searchable=strcat(
        tostring(Properties), " ", tostring(Measurements), " ",
        tostring(column_ifexists("Message", "")), " ",
        tostring(column_ifexists("Data", "")), " ",
        tostring(column_ifexists("Details", "")), " ",
        tostring(pack_all()))
| where Searchable contains canary
| project TimeGenerated, TableName, OperationId,
        ReferencedType=column_ifexists("ReferencedType", ""),
        ReferencedItemId=column_ifexists("ReferencedItemId", "")
```

An empty result is necessary but not sufficient. Also inspect exporter offline
storage, console output, SDK self-diagnostics, the durable record, cache, and audit
sink. KQL cannot prove absence from telemetry dropped before ingestion.

#### Orchestration p95

Prefer the dedicated orchestration span because subtracting independently sampled
dependency durations from request duration is unreliable:

```kusto
union AppRequests, AppDependencies
| where TimeGenerated >= ago(7d)
| where Name == "tokennexus.orchestration"
| extend
        AppId=tostring(Properties["tokennexus.application.id"]),
        SchemaVersion=tostring(Properties["tokennexus.telemetry.schema.version"])
| summarize
        Samples=count(),
        P50Ms=percentile(DurationMs, 50),
        P95Ms=percentile(DurationMs, 95),
        P99Ms=percentile(DurationMs, 99)
    by AppId, SchemaVersion, bin(TimeGenerated, 1d)
| extend MeetsNfr005=P95Ms <= 500
```

Release evidence requires at least 20 eligible timed requests and reports the
sample count beside p95.

### Golden OTLP Contract Tests

Golden tests should capture OTLP protobuf messages through a local receiver or
language-specific in-memory exporters, then normalize nondeterministic fields.
Do not golden-test exporter-specific console text or byte-for-byte protobuf order.

Normalize these fields before comparison:

* Trace and span IDs, timestamps, durations, process ID, thread ID, host name, and
    service instance ID
* Attribute order and protobuf field order
* SDK-generated scope and distribution patch versions, while separately asserting
    that allowed versions match the release manifest
* Azure resource-detector values not controlled by the fixture

Assert these invariants exactly:

* One product-root span and the required product operations
* One trace ID per synchronous fixture and correct parent or link relationships
* At most two paid attempts and no third attempt
* Required attribute names, types, enums, units, and schema version
* Native GenAI fields normalized to the selected compatibility profile
* Sensitive fields and canaries absent from spans, events, logs, metrics, baggage,
    and exporter diagnostics
* Metric names, units, aggregation type, and dimension allowlist
* Log severity, trace correlation, and fixed-template event names
* Azure sampling metadata and coherent parent decisions
* Bounded export queues, successful flush, and deterministic shutdown

Maintain the same scenario corpus for Python and .NET. Compare each runtime to its
own raw golden and both to one normalized semantic golden. Required scenarios are
success, cache hit, sensitive bypass, low-quality escalation, policy/budget/latency
non-escalation, provider timeout, evaluator unavailable, denied tool, approved
tool, sampled-out trace, exporter failure, and cancellation.

### Claims Requiring Live Backend Integration

The following claims cannot be closed by documentation or in-memory tests:

* Exact mapping of every Agent Framework and TokenNexus span kind to
    `AppRequests` versus `AppDependencies`
* Exact `Properties` key encoding for dotted names, arrays, booleans, numeric
    values, and nulls in the pinned Python and .NET exporters
* Native GenAI span names, source names, parentage, links, metrics, and semantic-
    convention mode for the selected Agent Framework packages
* Correct `OperationId`, `ParentId`, `ItemCount`, role name, role instance, and
    resource attribution across each service boundary
* Trace-based log-sampling defaults and correlation under the selected package
    versions
* Application Insights Agent details rendering and its dependence on specific
    GenAI attributes
* `AppGenAIContent` routing, pointer fields, protected-table behavior, and feature
    flag availability in the target subscription before and after September 30,
    2026
* `_BilledSize`, `_IsBillable`, ingestion latency, offline-storage retry, daily-cap
    overshoot, and actual regional cost
* Effective granular RBAC and inherited-role behavior for intended personas,
    alert managed identities, and protected tables
* Hosted MCP trace propagation and any cross-provider trace-context behavior
* KQL query compilation and results against the release workspace schema

Run one known fixture per scenario against the release Application Insights
resource and preserve the OTLP capture, KQL output, package lock files, resource
configuration, and evidence manifest.

### Primary-Document Updates

Update the primary implementation research during synthesis with these findings:

1. Replace the generic sampling recommendation with explicit Azure custom sampling:
     100% for acceptance and evaluation, 100% initially for low-volume production,
     and a measured 5% trial only when volume requires reduction.
2. Add the September 30, 2026 `AppGenAIContent` migration and protected-table
     requirement to privacy, schema migration, and rollout gates.
3. Record the stack choices as alternatives: Python uses
     `azure-monitor-opentelemetry` plus Agent Framework activation; ASP.NET Core uses
     `Azure.Monitor.OpenTelemetry.AspNetCore`; .NET workers use the exporter package.
4. State that Python and .NET Agent Framework workflow spans differ and contract
     tests compare normalized semantics rather than identical raw names.
5. Add `_BilledSize` and `_IsBillable` measurement as the authoritative ingestion-
     cost method, with regional price lookup and Cost Management reconciliation.
6. Add table-level retention, daily-cap alerts, `Log Analytics Data Reader` with
     granular conditions, protected GenAI content, and inherited-role validation.
7. Add the four KQL evidence patterns and the two-level golden test model.
8. Replace the old GenAI documentation URLs with the standalone semantic-
     conventions repository and mark it unreleased with no finalized schema URL.
9. Add a release-blocking live backend mapping test for both candidate stacks.

## Clarifying Questions

* Which implementation stack and exact package versions will be frozen?
* Which Application Insights resource, workspace, region, and Azure offer will
    determine price and availability?
* What production request volume, span count, log volume, and diagnostic fidelity
    justify sampling below 100%?
* Which privacy regime and evidence-retention policy govern metadata and any
    controlled content capture?
* Which identities require workspace, table, row, alert, and evidence-store access?
* Will all content capture be prohibited, or is an isolated, time-bounded diagnostic
    path required?
* Which release owner approves telemetry schema changes and the GenAI compatibility
    profile?

## References

### Primary Sources

* [Enable OpenTelemetry in Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-enable)
* [Configure OpenTelemetry in Application Insights](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-configuration)
* [Add and modify OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-add-modify)
* [Application Insights telemetry data model](https://learn.microsoft.com/en-us/azure/azure-monitor/app/data-model-complete)
* [Application Insights OpenTelemetry sampling](https://learn.microsoft.com/en-us/azure/azure-monitor/app/opentelemetry-sampling)
* [Migrate to Azure Monitor OpenTelemetry](https://learn.microsoft.com/en-us/azure/azure-monitor/app/migrate-to-opentelemetry)
* [Microsoft Agent Framework agent observability](https://learn.microsoft.com/en-us/agent-framework/agents/observability)
* [Microsoft Agent Framework workflow observability](https://learn.microsoft.com/en-us/agent-framework/workflows/observability)
* [Azure Monitor Logs cost calculations](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/cost-logs)
* [Azure Monitor pricing](https://azure.microsoft.com/en-us/pricing/details/monitor/)
* [Manage Log Analytics data retention](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/data-retention-configure)
* [Set a Log Analytics daily cap](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/daily-cap)
* [Manage Log Analytics access](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-access)
* [Granular RBAC in Log Analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/granular-rbac-log-analytics)
* [Manage table-level access](https://learn.microsoft.com/en-us/azure/azure-monitor/logs/manage-table-access)
* [OpenTelemetry GenAI semantic conventions repository](https://github.com/open-telemetry/semantic-conventions-genai)
* [OpenTelemetry GenAI documentation](https://github.com/open-telemetry/semantic-conventions-genai/tree/main/docs/gen-ai)
* [OpenTelemetry Protocol exporter](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)
* [OpenTelemetry Python exporters](https://opentelemetry.io/docs/languages/python/exporters/)
* [OpenTelemetry .NET exporters](https://opentelemetry.io/docs/languages/net/exporters/)

### Workspace Evidence

* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/opentelemetry-agent-observability-research.md
* docs/prds/tokennexus-ai-framework-prd.md
