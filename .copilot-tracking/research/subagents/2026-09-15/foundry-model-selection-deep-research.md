---
title: Microsoft Foundry Model Selection Deep Research
description: Evidence-based provisional model strategy for TokenNexus-AI-Framework enterprise MVP routing
ms.date: 2026-09-15
ms.topic: research
---

## Research Scope

* Identify economical and capable Microsoft Foundry model aliases for a general enterprise MVP
* Compare credible candidate pairs across capability, context, structured output and tools, latency and cost posture, deployment, identity and networking, lifecycle, evaluation, and portability
* Distinguish Global Standard, Data Zone Standard, Regional Standard, and serverless deployment options where applicable
* Define quota and capacity checks, alias and upgrade policy, and model-selection gates
* Select a provisional strategy without claiming subscription-specific availability

## Sources Reviewed

### Product and architecture sources

* docs/prds/tokennexus-ai-framework-prd.md
* .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
* .copilot-tracking/research/subagents/2026-09-15/azure-ai-foundry-deployment-research.md

The PRD requires two provider-neutral tiers, stable aliases, structured evidence,
one governed escalation, a bounded tool path, paired evaluation, deterministic
substitutes, cost controls, and portability. The deployment research separately
selects an application-hosted control plane on Azure Container Apps with Foundry
serverless model endpoints.

### Microsoft sources

* [Models sold directly by Azure](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/models-sold-directly-by-azure)
* [Microsoft Foundry deployment types](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types)
* [Model versions in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/model-versions)
* [Model lifecycle and support policy](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirements)
* [Model retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule)
* [Quota for Microsoft Foundry Models](https://learn.microsoft.com/azure/foundry/openai/how-to/quota)
* [Compare model benchmarks](https://learn.microsoft.com/azure/foundry/how-to/benchmark-model-in-catalog)
* [Evaluate generative AI applications](https://learn.microsoft.com/azure/foundry/how-to/develop/evaluate-sdk)
* [Role-based access control in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)
* [Network isolation for Foundry](https://learn.microsoft.com/azure/foundry/how-to/configure-private-link)
* [Foundry Models pricing](https://azure.microsoft.com/pricing/details/ai-foundry-models/)

Microsoft catalog and benchmark material is suitable for shortlisting, not final
selection. The catalog changes, benchmark results are not TokenNexus workload
results, and deployability depends on the target subscription, region, model
version, and deployment type.

## Findings

### Decision drivers

The economical alias is not the smallest model available. It is the least costly
eligible deployment that meets the frozen request contract and quality threshold.
The capable alias is not an unconditional frontier default. It is the higher-quality
deployment used for direct high-risk routing or one permitted escalation.

Both aliases need to satisfy the same minimum contract:

* supported serverless API deployment in the intended Foundry resource
* stable text generation and JSON-schema-constrained output for product contracts
* bounded function or tool calling for the protected-tool demonstration
* sufficient context and output limits for the selected reference use case
* token accounting and finish-state metadata required by the execution journal
* Microsoft Entra authentication from the control-plane managed identity
* compatible content-filter, data-processing, and private-network posture
* an active lifecycle window long enough to operate and replace the deployment

### Candidate comparison

| Candidate strategy | Economical tier | Capable tier | Strengths | Material gaps or risks | Disposition |
| --- | --- | --- | --- | --- | --- |
| Current same-family GPT pair | `gpt-5.4-mini` | `gpt-5.4` | Shared Responses-style contract, structured outputs, multimodal input, tools, and generous output limits reduce adapter and escalation drift. The larger model is a natural quality challenger to the mini tier. | Current price, regional support, quota, latency, model-version behavior, and retirement status are dynamic. A newer family also has less workload history than established alternatives. | Provisional baseline, subject to every live and evaluation gate |
| Established GPT-4.1 pair | `gpt-4.1-mini` | `gpt-4.1` | Mature non-reasoning family with long-context support, structured outputs, and tools. Useful as a stability and latency challenger. | May lose quality or efficiency to newer models; lifecycle horizon and price must be checked at selection time. | Mandatory benchmark challenger when both deployments are eligible |
| Mixed Mistral pair | Mistral small model | Mistral large model | Adds provider diversity and can support JSON and tool-oriented workloads on eligible offerings. May offer an attractive cost or latency profile. | Exact APIs, tool semantics, context/output limits, Marketplace terms, identity, networking, safety controls, and lifecycle differ by offer. Cross-provider escalation increases normalization work. | Conditional challenger, not the default pair |
| Phi-4 economical tier | Phi-4 small or mini variant | GPT or larger partner model | Potentially attractive for narrow classification, extraction, or summarization after task-specific evaluation. Improves provider and deployment portability. | Current catalog variants do not provide the same general tool-calling contract needed by the full MVP path. Smaller context or output limits and mixed-provider escalation create feature asymmetry. | Use only for a tool-free route or after the MVP contract is split by capability |
| Independent best-of-breed pair | Lowest-cost passing model from any provider | Highest-utility passing model from any provider | Maximizes theoretical price-performance for a frozen workload. | Highest adapter, safety, identity, lifecycle, and observability variance. A passing point-in-time benchmark can conceal operational drift. | Future optimization after the provider-neutral adapter and conformance suite are proven |

The same-family GPT strategy wins provisionally because TokenNexus is itself the
economics experiment. Holding the provider contract relatively constant makes the
first paired results easier to interpret: measured differences are less likely to
come from incompatible tool schemas, finish reasons, usage accounting, or content
filter behavior. This is an experimental-control advantage, not a permanent vendor
preference.

Phi-4 and Mistral remain useful challengers. Phi is strongest where a route can be
declared tool-free and narrowly scoped. Mistral is stronger when provider diversity
or measured price-performance outweighs the additional conformance burden. Neither
should be inserted into an alias merely because its catalog label implies lower cost.

### Deployment type decision

| Deployment type | Processing and capacity posture | TokenNexus use |
| --- | --- | --- |
| Global Standard | Azure can route processing globally within the documented geography model. It generally offers the broadest availability and is the normal starting point for variable pay-as-you-go traffic. | Preferred MVP default only when the data-processing policy permits it |
| Data Zone Standard | Processing stays within the selected United States or European Union data zone, subject to the service terms and model support. Availability can be narrower than Global Standard. | Preferred when zone-level residency is required and the selected models pass live checks |
| Regional Standard | Processing stays in the deployment region. Model and regional capacity can be more constrained. | Use when the use case requires regional processing and the full dependency path supports it |
| Provisioned | Purchased throughput gives more predictable capacity for suitable stable workloads. Quota approval and current capacity remain separate considerations. | Defer until observed traffic, utilization, latency, and cost demonstrate a benefit |
| Batch or priority processing | Specialized price, latency, and scheduling tradeoffs do not match the default synchronous request path. | Evaluate later for offline evaluation jobs or an explicitly premium request class |

Use the serverless API plane selected by the deployment research. Do not choose
managed compute merely to host a catalog model that already has an eligible
serverless deployment. Managed compute introduces dedicated sizing, utilization,
runtime, preview, and GPU-capacity concerns that are not justified by the MVP.

### Quota, capacity, and availability

Foundry quota is scoped by dimensions that include subscription, region, model,
and deployment type. An available quota allocation does not guarantee that Azure
can create a deployment at that moment. Provisioned-throughput quota likewise does
not reserve underlying capacity before deployment or reservation succeeds.

Catalog visibility also does not prove deployability. Model availability can differ
by subscription type, region, offer, version, deployment SKU, safety approval, and
Marketplace access. The deployment record must therefore capture the result of a
live preflight rather than treating a research-time catalog result as evidence.

### Identity, networking, and commercial terms

Use Microsoft Entra authentication from the Container App managed identity whenever
the selected model endpoint supports it. Grant the narrow runtime inference role at
the smallest workable scope and keep model deployment administration separate from
runtime invocation. Do not place API keys in source, evaluation manifests, or traces.

Validate private networking end to end before disabling public access. Control-plane
ingress, Foundry resource access, model-provider endpoints, DNS, and bounded tools are
separate paths. A private endpoint on one resource does not prove that a partner
model or tool remains reachable through the intended path.

Partner models can require Marketplace subscription, separate provider terms, or a
different billing and support relationship. Those checks are release gates for
Mistral, Cohere, Meta, DeepSeek, and other non-Azure OpenAI candidates, not paperwork
to defer until after an alias is configured.

### Evaluation is the selection authority

Foundry catalog benchmarks are screening evidence. The frozen TokenNexus evaluation
manifest is the selection authority. Run every candidate through identical inputs,
request options, tool contracts, evaluator versions, price snapshots, warm-up rules,
and concurrency conditions.

At minimum, compare:

* task success and evaluator score by request class
* JSON-schema validity and repair or retry frequency
* tool-selection accuracy, argument validity, and prohibited-call rate
* first-token, end-to-end, and model-only latency distributions
* input, cached-input, output, and reasoning token usage where exposed
* estimated cost per successful request and per quality-adjusted successful request
* content-filter and refusal outcomes
* timeout, throttling, and provider-error behavior
* direct-capable routing, economical success, and one-step escalation rates

The PRD minimum of 30 paired requests can demonstrate the product flow but is too
small to establish broad production superiority. Treat it as an MVP acceptance set,
report individual outcomes and uncertainty, and expand the corpus before making a
high-confidence economic or quality claim.

### Alias, version, and rollback policy

The logical aliases must resolve through versioned configuration, not model names in
application code. Record at least the provider, physical deployment, model name,
model version, deployment type, region or zone, content-filter configuration,
upgrade policy, and price-manifest version for each resolution.

Do not switch an alias in place without a parallel candidate deployment. Create the
replacement, run conformance and frozen evaluation, approve the comparison, update
the alias configuration, observe a canary cohort, and retain the prior deployment
until rollback evidence is complete.

Automatic version upgrades can change behavior without an application release.
Select and record the Foundry upgrade option deliberately. Production aliases should
not depend on an undocumented default. Monitor lifecycle metadata, retirement notices,
Service Health, and the published retirement schedule. An opt-out policy is not an
indefinite support guarantee; a retired deployment must be migrated.

## Provisional Recommendation

Provisionally resolve the aliases as follows:

```yaml
model_aliases:
  economical:
    candidate_model: gpt-5.4-mini
    candidate_deployment_type: GlobalStandard
    status: provisional
  capable:
    candidate_model: gpt-5.4
    candidate_deployment_type: GlobalStandard
    status: provisional
```

`GlobalStandard` is a starting assumption, not a residency decision. Replace it with
Data Zone Standard or Regional Standard when Q-009 establishes the corresponding
processing constraint and both candidate models are deployable there.

The pair becomes the MVP baseline only after all of these gates pass:

1. Both exact model versions and deployment types are deployable in the target
   subscription and approved geography.
2. Assigned quota and observed capacity support the evaluation load plus an agreed
   operational margin.
3. The managed identity can invoke both endpoints without stored model keys.
4. Required private networking and content-filter behavior work for both endpoints.
5. Both models pass the common adapter conformance suite for JSON, usage, errors,
   cancellation, timeouts, and bounded tools.
6. `gpt-5.4-mini` meets the economical quality floor on the frozen corpus.
7. `gpt-5.4` produces a material quality or success improvement on the cases eligible
   for direct capable routing or escalation.
8. The combined route meets the PRD latency and budget policies using a frozen price
   manifest and measured token usage.
9. Lifecycle dates and the selected version-upgrade policy leave enough time for the
   parallel replacement procedure.
10. The complete paired report is approved by product, FinOps, platform, and security
    owners.

If the economical candidate fails, benchmark `gpt-4.1-mini` first, then an eligible
Mistral small offering, and use Phi-4 only for a separately declared tool-free route.
If the capable candidate fails, benchmark `gpt-4.1` and an eligible Mistral large
offering. Do not silently substitute a candidate: preserve the failed gate and the
replacement decision in the evaluation evidence.

Start with pay-as-you-go Standard capacity. Reassess provisioned throughput only
after production-like measurements show stable demand and compare total cost at the
required throughput and latency. This prevents the MVP from converting an uncertain
traffic forecast into an idle capacity commitment.

## Dynamic Facts Requiring Live Checks

Complete this checklist immediately before infrastructure planning and repeat it
before each model promotion:

| Check | Required evidence | Blocking condition |
| --- | --- | --- |
| Subscription and tenant | Approved subscription ID, tenant ID, resource provider registration, and policy status | Target context is unknown or disallowed |
| Catalog and offer | Exact model ID, provider, version, offer terms, Marketplace subscription, and support channel | Offer cannot be subscribed to or governed |
| Geography | Approved region or data zone and processing-residency interpretation | Q-009 is unresolved or deployment type violates it |
| Deployment support | Exact model, version, SKU, and deployment type shown as deployable | Portal or API does not offer the intended combination |
| Quota | Available and assigned TPM, RPM, or PTU dimensions for each deployment | Evaluation and operating headroom cannot be allocated |
| Capacity | Successful deployment or current capacity confirmation | Quota exists but deployment creation fails for capacity |
| Pricing | Dated input, cached-input, output, reasoning, batch, priority, and provisioned prices as applicable | Price manifest is incomplete or stale |
| Identity | Managed-identity token acquisition and inference authorization test | Runtime requires an unapproved key or excessive role |
| Networking | DNS, public-access policy, private endpoint, egress, firewall, and provider-path test | Intended production path cannot reach an endpoint |
| Safety | Content-filter configuration and seeded safety-case results | Filters cannot meet the approved policy |
| API behavior | Structured-output, tool, token-usage, error, timeout, and cancellation conformance | Common adapter would need alias-specific product behavior |
| Performance | Warm and cold latency, concurrency, throttling, and timeout results | PRD latency or reliability gate fails |
| Quality | Frozen evaluator and human-review results by request class | Economical floor or capable uplift gate fails |
| Lifecycle | Lifecycle state, deprecation and retirement information, upgrade option, and replacement lead time | No supported operating and migration window remains |

Do not copy numeric prices from this research into policy. Generate a dated,
source-attributed price manifest from the current Azure pricing surface for the exact
offer, meter, geography, and deployment type. Preserve that manifest with each
evaluation run so historical cost comparisons remain reproducible.

## Blockers and Clarifying Questions

### Blocks final model selection

* Q-003: the reference use case, domain, languages, modalities, and risk classes are
  not frozen.
* Q-005: the evaluator, rubric, threshold, expected labels, and human-review protocol
  are not frozen.
* Q-006: request budgets, context/output ceilings, latency deadlines, and concurrency
  assumptions are not approved.
* Q-008: subscription, region, environments, capacity allocation, traffic forecast,
  and operating budget are unknown.
* Q-009: data classification, residency, privacy, and regulatory obligations are
  unresolved.
* The target subscription has not been checked for offer access, quota, current
  capacity, pricing, or regional availability.

### Clarifying questions

* Must every request class support tools, or can TokenNexus declare a lower-cost
  tool-free capability class?
* Is multimodal input part of the MVP evaluation or merely a future compatibility
  preference?
* What minimum quality uplift justifies capable-tier cost and escalation latency?
* Is Global Standard processing acceptable, or must processing stay within a data
  zone or one Azure region?
* Who owns alias promotion, emergency rollback, price-manifest refresh, and model
  retirement response?
* How much operational headroom above the measured evaluation load must quota and
  capacity provide?

## Exact Primary-Document Updates

Apply the following changes to
.copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md
after the unresolved owners approve the provisional strategy. This research task does
not edit that primary document.

### Replace the unresolved model-selection statement

Replace the current generic instruction to select two models with:

> Provisionally benchmark `gpt-5.4-mini` as `economical` and `gpt-5.4` as
> `capable`. Treat this as a same-family experimental baseline, not a final
> availability or procurement decision. Promote the pair only after frozen
> workload evaluation and live subscription, region, deployment type, quota,
> capacity, price, identity, networking, safety, lifecycle, and retirement gates.

### Add candidate challengers

Add this paragraph to the model-serving section:

> Run `gpt-4.1-mini` and `gpt-4.1` as the mandatory established-family
> challengers when eligible. Evaluate Mistral small and large offerings when
> provider diversity or measured price-performance could justify extra adapter
> variance. Restrict Phi-4 candidates to declared tool-free routes until an exact
> catalog variant passes the common tool contract.

### Add the deployment-type rule

Add this decision beneath the serverless recommendation:

> Start with Global Standard only when processing policy permits it. Use Data Zone
> Standard for approved United States or European Union zone processing and
> Regional Standard when processing must remain in one deployment region. Recheck
> exact model support and capacity for every choice. Defer provisioned throughput
> until measured stable demand establishes a throughput, latency, or total-cost
> advantage.

### Add alias lifecycle controls

Add these requirements to the deployment lifecycle:

* resolve aliases through versioned configuration and record physical deployment,
  model version, deployment type, geography, content filter, upgrade option, and
  price-manifest version
* replace models through parallel deployments, frozen evaluation, canary promotion,
  retained rollback, and recorded approval
* monitor lifecycle metadata, retirement notices, Service Health, and the published
  retirement schedule
* prohibit undocumented automatic upgrade behavior on production aliases

### Update Q-004 status without closing it

Change Q-004 from an unbounded model question to:

> Provisional answer: `gpt-5.4-mini` for `economical` and `gpt-5.4` for
> `capable`, initially using an eligible Standard serverless deployment. Status
> remains open until workload evaluation and target-subscription gates pass.

### Add a research reference

Append this artifact to the source list:

* .copilot-tracking/research/subagents/2026-09-15/foundry-model-selection-deep-research.md

Status: Complete for provisional model strategy and evaluation/deployment gates.
Final selection remains blocked by product decisions and live target-subscription
evidence.
