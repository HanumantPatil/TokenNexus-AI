---
title: Azure AI Foundry Deployment Research for TokenNexus-AI-Framework
description: Evidence-based comparison and recommendation for deploying the TokenNexus-AI-Framework control plane and its model dependencies
ms.date: 2026-09-15
ms.topic: architecture
---

<!-- markdownlint-disable MD060 -->

## Research Scope

Research Azure AI Foundry deployment options for TokenNexus-AI-Framework based on the product requirements in docs/prds/tokennexus-ai-framework-prd.md.

Questions under investigation:

* How do Foundry prompt agents, Foundry hosted agents, and application-hosted Microsoft Agent Framework orchestration compare for this product?
* When are Azure Container Apps, App Service, or AKS appropriate for the control plane?
* How do serverless and managed-compute model deployments differ?
* What constraints apply to private networking, managed identity, RBAC, scaling, quotas, regional availability, deployment lifecycle, evaluation, and observability?
* How should model deployment be separated from control-plane hosting?
* Which topology best fits the MVP, and how should it evolve for production?
* Which deterministic local substitutes preserve testability and repeatability?

## Executive Decision

Use an application-hosted TokenNexus control plane on Azure Container Apps and
invoke two Microsoft Foundry serverless model deployments through a
provider-neutral adapter. Keep routing, cost estimation, semantic caching,
quality evaluation, escalation, authorization, and evidence generation in the
TokenNexus application. Do not implement the MVP as a Foundry prompt agent or
host the control plane on AKS.

This topology best fits the product boundary in the PRD. TokenNexus makes a
deterministic, policy-governed decision before model invocation and must expose
stable APIs, reason codes, model aliases, policy versions, budget outcomes, and
authorization evidence. Those are application control-plane responsibilities,
not model-serving responsibilities.

Use Foundry hosted agents later only for a bounded agent or tool path that has
an independently valuable agent lifecycle. Use managed-compute model
deployments only when a selected open-source, partner, or custom model cannot be
served through the preferred serverless API and preview status is acceptable.

## PRD Decision Drivers

The recommendation is grounded in these exact PRD locations:

| PRD lines | Requirement or constraint | Deployment consequence |
|-----------|---------------------------|------------------------|
| 25-47 | The product is an economics control plane with measurable routing, cost, quality, telemetry, usability, and evidence goals | The application must own policy and measurement rather than delegate the request lifecycle to a general-purpose agent |
| 94-106 | The MVP includes two model tiers, policy routing, caching, evaluation, escalation, telemetry, authorization, a bounded tool path, and deterministic substitutes | A stable application service with replaceable model and dependency adapters is the primary unit of deployment |
| 108-117 | Production availability, broad framework support, and multi-agent autonomy are out of scope | Avoid AKS and a multi-agent topology for MVP |
| 121-128 | Two model tiers are assumed, while quota, budget, provider availability, and evaluator quality are constrained | Model deployments need independent capacity checks, aliases, and fallback procedures |
| 152-159 | The conceptual flow validates, estimates, applies policy, invokes a model, evaluates quality, escalates, responds, and records telemetry | The control plane is a request orchestrator; the model endpoint is one downstream dependency |
| 170-189 | FR-001 through FR-020 define routing, budget, cache, evaluation, escalation, evidence, protected actions, and bounded tools | Prompt-only orchestration is insufficient; server-side application code must enforce these rules |
| 181-185 | FR-012 requires provider-neutral models, FR-013 controlled degradation, FR-014 protected content, and FR-016 server-side role checks | Model clients and infrastructure integrations must be injected behind interfaces and authorization must run in the API |
| 195-206 | NFR-001 through NFR-012 require privacy, timeouts, 500 ms p95 orchestration overhead, deterministic substitutes, portability, deny-by-default authorization, and resource bounds | Prefer a stateless, autoscaled application host with local fakes and explicit dependency policies |
| 231-245 | The instrumentation plan separates policy, cache, model, quality, completion, protected-action, and feedback events | Application Insights traces must preserve component spans and redact prompt and response content by default |
| 248-257 | Model deployments, embeddings/cache, prices, evaluator, telemetry, and the evaluation manifest are separate dependencies | Provision and version each dependency independently; do not combine the control plane with model compute |
| 264-268 | Dynamic routing, quota outages, and reproducibility are high risks | Pin evaluation inputs and aliases, monitor capacity, and evaluate replacement models before switching aliases |
| 293-303 | Deployment, configuration, rollback, monitoring, support, and capacity procedures are required | Use infrastructure as code, immutable app revisions, versioned configuration, alerts, and a recorded capacity gate |
| 305-321 | Release gates begin with deterministic adapters and end with rollback, evidence, and support ownership | Deploy incrementally and do not make private networking or AKS prerequisites for MVP acceptance |
| 326-337 | Model tiers, evaluator, policies, cache rules, hosting, capacity, budget, and privacy remain open | Final provisioning cannot be sized or region-locked until these decisions are resolved |

Source: docs/prds/tokennexus-ai-framework-prd.md.

## Separate the Two Deployment Planes

Treat model deployment and control-plane hosting as independent decisions.

| Plane | Owns | Recommended MVP service | Changes independently when |
|-------|------|-------------------------|----------------------------|
| TokenNexus control plane | Public API, request validation, user and application authorization, policy engine, price lookup, semantic cache, evaluator orchestration, one-step escalation, telemetry, decision summary, and bounded tools | Azure Container Apps | Policy code, API schema, UI, cache behavior, evaluators, authorization, or telemetry changes |
| Model serving | Model weights/runtime, inference endpoint, deployment SKU, quota consumption, provider/model version, and content-filter configuration | Two Foundry serverless API deployments | Model version, provider, region, deployment type, quota, price, or retirement changes |

The boundary is a provider-neutral model interface with stable TokenNexus request
and response types. Configuration maps logical aliases such as `economical` and
`capable` to physical Foundry deployment names. Execution records store both
the logical alias and resolved provider, model, and version. This design lets a
model deployment be replaced without changing the TokenNexus API or policy
domain model, as required by FR-012 and NFR-008.

Foundry Agent Service hosting is a third concern, not a replacement for either
plane. It can host an agent implementation and manage its endpoint, identity,
sessions, and scaling, but TokenNexus still needs an application boundary for
its economics and governance contract.

## Agent and Orchestration Options

| Option | Runtime ownership | Fit for TokenNexus | Networking and identity | Scaling and operations | Decision |
|--------|-------------------|--------------------|-------------------------|------------------------|----------|
| Foundry prompt agent | Foundry manages a declarative prompt, tools, model selection, endpoint, and service runtime | Weak for the core control plane. It is suitable for prompt-led behavior, but the PRD requires deterministic pre-inference policy, budget enforcement, cache semantics, stable reason codes, protected actions, and detailed economics records | Uses Foundry project identity, connections, RBAC, and Agent Service network options. Network isolation support depends on agent type and tool | Lowest application-hosting effort, but custom control logic is constrained by the declarative surface | Do not use for the core MVP. It may implement a bounded demonstration agent behind the control plane |
| Foundry hosted agent | The team supplies custom code and dependencies; Foundry manages hosting, endpoint, identity, sessions, scaling, and container infrastructure | Better than a prompt agent for custom agent code, but its managed agent lifecycle does not remove TokenNexus API, policy, cache, evaluator, authorization, and evidence responsibilities | Supports managed identity and Foundry RBAC. Private networking and tool connectivity require validation against the current hosted-agent support matrix | Lower infrastructure effort than self-hosting, with less control over the surrounding web application topology | Consider for a future bounded agent or long-running tool workflow, not as the MVP control plane |
| Application-hosted Microsoft Agent Framework | The application owns its HTTP boundary, routing, authorization, request policy, state/storage choices, deployment, and scaling; Agent Framework supplies orchestration abstractions | Strongest fit when agent capabilities are needed because the product retains exact control of the request and evidence lifecycle | Uses the host's managed identity, network, RBAC, and secrets model. It can call Foundry models or agents as dependencies | Host-dependent. Container Apps provides the required managed runtime without surrendering application behavior | Preferred orchestration posture. Use Agent Framework only where it adds value; ordinary application services remain appropriate for deterministic policy paths |

Microsoft states that Microsoft Agent Framework can be hosted in Foundry or
self-hosted, and that hosting choice is independent of the agent protocol. The
key distinction is operational ownership. Self-hosting retains application
control; Foundry hosting supplies managed agent lifecycle infrastructure.

## Control-Plane Hosting Options

| Dimension | Azure Container Apps | Azure App Service | Azure Kubernetes Service |
|-----------|----------------------|-------------------|----------------------------|
| Workload fit | Containerized API or microservice with HTTP/event-driven autoscaling | Conventional web/API application with a supported runtime or custom container | Multi-workload Kubernetes platform or workload requiring Kubernetes APIs, operators, custom scheduling, service mesh, or cluster-level controls |
| Scaling | KEDA-based HTTP or event scaling; most workloads can scale to zero; minimum replicas can avoid cold starts | Plan-based scale-out and Azure Monitor autoscale; instances and cost are coupled to the App Service plan | Horizontal/vertical pod autoscaling, KEDA, node autoscaling, and custom Kubernetes policies; the team owns application and node-pool sizing |
| Releases | Immutable revisions, single or multiple revision modes, traffic splitting, labels, and rollback | Deployment slots support warm-up, smoke tests, swap, and swap-back rollback on Standard or higher plans | Deployments, services, ingress, GitOps, and rollout controllers provide maximum control but require Kubernetes operations |
| Networking | Internal ingress, VNet integration, and Private Link for workload-profile environments; private endpoints require disabling public network access and private DNS | Private endpoints for inbound access and VNet integration for outbound access on supported plans | Most configurable networking and isolation, with corresponding cluster, ingress, DNS, and policy responsibility |
| Identity and secrets | System- or user-assigned managed identity; Key Vault references and RBAC | System- or user-assigned managed identity; Key Vault references and RBAC | Microsoft Entra Workload ID, managed identities for Azure resources, Kubernetes RBAC, and secret-store integration |
| Operational burden | Medium: container image and registry are required, while Azure manages orchestration | Low: code or container deployment on a managed web platform | Highest: even with managed control plane or AKS Automatic, Kubernetes resources, workload configuration, governance, and day-2 skills remain necessary |
| MVP assessment | Best balance of portability, revisions, autoscaling, managed identity, and future microservice growth | Valid alternative if the implementation becomes a conventional single web app and deployment slots are preferred over container revisions | No current PRD requirement justifies the added control or operational cost |

Select Container Apps for MVP. Set a minimum replica of one for performance
testing and release environments so scale-to-zero cold starts do not invalidate
the 10-second end-to-end and 500 ms orchestration targets. A development
environment may scale to zero to reduce cost. Keep the API stateless and place
cache and durable records in external services.

App Service is the fallback, not a poor choice. Select it if the eventual code
base is a conventional supported-runtime web application, the team does not
want a container supply chain, and deployment slots are more valuable than
KEDA, revisions, or native microservice growth.

Select AKS only after a concrete requirement appears, such as a Kubernetes
operator, custom scheduler, advanced network plug-in, cluster-level policy,
shared multi-workload platform, service mesh, or specialized node topology.
Microsoft's service-selection guidance identifies AKS as the most customizable
option and also the option requiring the most operational input.

## Model Deployment Options

| Dimension | Foundry serverless API deployment | Foundry managed-compute deployment |
|-----------|------------------------------------|------------------------------------|
| Compute model | Microsoft or the model provider operates shared service infrastructure behind an API deployment | Azure provisions dedicated managed compute for the deployed model |
| Best fit | Supported catalog models, rapid start, API-based inference, bursty or uncertain MVP demand, and no need to manage GPU capacity | Open-source, partner, or custom models that require dedicated compute, model artifacts, custom runtime settings, or predictable reserved hardware |
| Cost and scaling | Consumption-oriented pricing and service-managed scale, subject to model, SKU, quota, and capacity | Compute is allocated and billed while provisioned; the team must size instances and understand startup, upgrade, and utilization behavior |
| Availability | Preferred Foundry deployment route when the selected model supports it; model, version, SKU, and region combinations vary | Preview at the time of research; region, VM/GPU SKU, and model support are narrower |
| Networking and identity | Endpoint authentication and private networking depend on model provider and deployment type; validate Microsoft Entra ID and private-link support for each selected model | Network and identity configuration also depend on managed-compute capabilities and preview limitations |
| Lifecycle | Deployment aliases can point to pinned model versions; standard deployment types support configurable automatic-upgrade policies | Treat runtime and model artifacts as independently versioned; preview changes and dedicated capacity increase operational risk |
| TokenNexus decision | Use two deployments behind `economical` and `capable` aliases | Defer unless a chosen model is unavailable serverlessly or dedicated compute is a measured requirement |

Serverless is the recommendation, not a guarantee of zero capacity work. Foundry
quota is scoped by subscription, region, model, and deployment type, and quota
does not guarantee current deployment capacity. Before provisioning, verify the
two chosen models, versions, SKUs, regions, token-per-minute and request limits,
authentication mode, content-filter behavior, and replacement availability.

## Selected MVP Topology

1. A reference client authenticates with Microsoft Entra ID and calls the
   TokenNexus HTTPS API.
2. One Azure Container App hosts the stateless API and deterministic
   orchestration path. The API validates roles server-side and denies protected
   actions by default.
3. The container app uses managed identity and least-privilege RBAC to access
   supported Azure dependencies. No model key is stored in source or emitted in
   traces.
4. Versioned configuration maps the `economical` and `capable` aliases to two
   Foundry serverless model deployments and stores fixed evaluation prices,
   policy values, thresholds, cache rules, and timeouts.
5. The API checks an external semantic cache, invokes the selected model through
   the common adapter, evaluates the result, and performs at most one governed
   escalation.
6. Application Insights receives OpenTelemetry traces and custom execution
   events. Prompt and response capture is disabled or redacted by default.
7. A durable store holds execution metadata, policy versions, feedback, and
   evidence references. Raw model content is excluded unless an approved
   retention and redaction policy enables it.
8. Bicep and Azure Developer CLI definitions reproduce development, evaluation,
   and release environments. Deployment outputs contain resource identifiers,
   not credentials.

For the MVP, public HTTPS ingress protected by Entra authentication is adequate
unless the selected use case mandates private access. Private endpoints add
Private Link, DNS, subnet, access-path, and cost requirements. Plan address space
and DNS early, but introduce private ingress and private Foundry connectivity in
the production hardening stage after verifying that every chosen model and tool
supports the required network path.

## Deterministic Local Substitutes

The repeatable acceptance suite must not depend on live model variability,
service quota, network timing, or mutable prices. Implement these substitutes
behind the same interfaces used by production:

| Production dependency | Deterministic substitute | Required assertions |
|-----------------------|--------------------------|---------------------|
| Economical and capable model adapters | Scripted model adapter keyed by fixture ID and logical model alias | Selected alias, request shape, call count, token fixture, latency fixture, response fixture, timeout, and provider-error paths |
| Quality evaluator | Table-driven evaluator returning frozen score, version, and unavailable states | Threshold behavior, one-step escalation, non-escalation reason, and linked attempt IDs |
| Semantic cache and embedding similarity | In-memory scoped cache plus curated similarity fixture | Hit, miss, stale, sensitive, freshness-critical, cross-scope isolation, expiry, and bypass behavior |
| Pricing source | Versioned local price manifest | Pre-execution estimate, all-frontier baseline, over-budget downgrade/block/approval, and visible assumptions |
| Telemetry sink | In-memory execution-event collector with schema validation | Event order, completeness, reason codes, redaction, component status, and correlation IDs |
| Identity and authorization | Signed test principal or in-process claims fixture | Authorized positive cases and denied policy, export, and cache actions without client dependence |
| Bounded tool adapter | Allowlisted fake tool registry with argument validators | Disallowed tool denial, bounded call count, cancellation, timeout, and seeded-secret protection |
| Clock and ID generation | Fixed clock and deterministic ID source | Stable cache age, expiration, event timestamps, request IDs, and linked attempts |

Use dependency injection so local fakes replace network clients without changing
the public request contract. Separate deterministic policy acceptance from live
model evaluation. The live suite can use frozen prompts, deployment aliases,
model versions, evaluator rubric, and prices, but its output should be assessed
with tolerances or semantic criteria and should run in a dedicated stage. It
must not be the only proof that budget, authorization, call bounds, or escalation
rules work.

## Security, Networking, and Access Control

* Authenticate users and calling applications with Microsoft Entra ID at the
  application boundary, then enforce product roles in TokenNexus server code.
* Assign a managed identity to the Container App. Grant only the data-plane
  actions needed for model invocation, telemetry, configuration, cache, and
  durable storage. Keep Foundry management roles separate from runtime roles.
* Store exceptional credentials in Azure Key Vault and prefer identity-based
  access. Never place provider keys in application settings when Entra
  authentication is supported.
* Disable raw prompt and response tracing by default. Record model alias,
  deployment/version identifiers, tokens, cost estimate, latency, evaluator
  version, cache state, escalation, reason codes, and component status.
* Validate network support per model, provider, agent type, and tool before
  disabling public access. Foundry Agent Service, model endpoints, and the
  Container Apps environment have distinct network controls.
* When private ingress is required, use a workload-profile Container Apps
  environment, disable public network access, create the private endpoint, and
  configure private DNS. Account for the additional Private Link and Container
  Apps management charges.

## Observability and Evaluation

Foundry and Agent Framework tracing integrate with Application Insights through
OpenTelemetry. Use one end-to-end trace ID and child spans for policy, cache,
model attempt, evaluator, telemetry enrichment, and bounded tool operations.
Emit the PRD events at lines 235-242 as structured events and validate required
fields in CI.

Maintain two evaluation lanes:

1. Deterministic policy acceptance runs locally and in every pull request. It
   proves routing, budget, cache, authorization, degradation, bounds, and event
   schemas with no paid inference.
2. Live model evaluation runs against pinned deployment aliases in a controlled
   environment. It compares TokenNexus and all-frontier behavior on the same
   versioned manifest and captures model/version, evaluator/version, prices,
   quota settings, and environment metadata.

Set alerts for model invocation failures and throttling, evaluator unavailable,
telemetry completeness degradation, budget blocks, elevated orchestration p95,
and cache failure. Keep model latency separate from orchestration latency so the
500 ms control-plane target remains diagnosable.

## Deployment Lifecycle and Production Evolution

### Stage 1: Deterministic foundation

Build the API, domain policy, execution schema, and all local substitutes. Run
the eight acceptance scenarios without Azure model dependencies. Provision no
AKS cluster and no managed GPU compute.

### Stage 2: Azure MVP evaluation

Deploy one Container App and two Foundry serverless model deployments. Set one
minimum replica in timed environments, configure managed identity and
least-privilege RBAC, connect Application Insights, freeze model aliases and
prices, and execute the paired evaluation manifest. Use Container Apps single
revision mode for safe default roll-forward behavior and retain the previous
revision for rollback evidence.

### Stage 3: Production hardening

Add separate staging and production resources, private networking where the
use case requires it, private DNS, zone redundancy where supported, a durable
cache and execution store, deployment health probes, alerts, budgets, support
ownership, backup/retention policies, and tested recovery. Use multiple
Container Apps revisions and controlled traffic splitting for canary releases.
Set minimum replicas from measured latency and concurrency rather than relying
on scale-to-zero.

### Stage 4: Scale and specialization

Add a secondary model deployment or region after failover behavior is defined
and tested. Introduce API Management only when centralized consumer governance,
rate limits, product subscriptions, or AI gateway policy justify it. Consider a
Foundry hosted agent for isolated agent workflows. Consider managed compute for
a measured model requirement. Move to AKS only when concrete Kubernetes-level
requirements outweigh the higher operational burden.

### Model replacement procedure

Treat model retirement as a release, not a transparent infrastructure event.
Foundry Standard-family deployments can automatically upgrade according to
their configured policy, while provisioned deployments are not automatically
upgraded. An opt-out deployment stops working after retirement if it is not
migrated.

1. Monitor the Foundry model retirement schedule, Service Health, and Models API
   lifecycle fields.
2. Create a parallel deployment for the replacement model rather than replacing
   the active alias immediately.
3. Run the frozen live evaluation and security tests against both deployments.
4. Review route accuracy, quality, cost, latency, content filtering, token
   behavior, and API-contract changes.
5. Change the logical alias through versioned configuration, canary the control
   plane if needed, retain rollback, and record the model migration evidence.

## Decision Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Serverless deployment quota exists but capacity is unavailable | MVP provisioning or scale-out fails | Check quota and current regional availability before region selection; keep model aliases and an approved secondary deployment procedure |
| Scale-to-zero adds cold-start latency | Acceptance latency becomes noisy or fails | Use one minimum replica for evaluation and release; measure before setting production minimums |
| Automatic model upgrade changes behavior | Routing, quality, cost, or reproducibility changes without application code | Choose and document the upgrade policy; use parallel deployments and alias changes after evaluation |
| Private networking is introduced before compatibility is known | A model, tool, or agent endpoint becomes unreachable | Validate the complete network path and provider support before disabling public access |
| Prompt or response content leaks through tracing | Privacy and evidence controls fail | Disable content capture by default, redact approved fields, and test exported traces |
| Foundry agent hosting absorbs product policy | Stable reason codes, budget rules, authorization, or deterministic tests become difficult to prove | Keep the TokenNexus control plane application-hosted and restrict agents to bounded adapters |
| Managed compute preview is treated as the default | MVP inherits GPU sizing, preview support, and utilization risk | Prefer serverless deployments and require an explicit exception for managed compute |
| AKS is selected for anticipated rather than current needs | Delivery slows and day-2 burden grows without product value | Require a documented Kubernetes-only capability before migration |

## References

### Microsoft Foundry and Agent Framework

* [Hosted agents in Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents)
* [Microsoft Foundry integrations for Agent Framework](https://learn.microsoft.com/agent-framework/integrations/by-provider/microsoft-foundry)
* [Understanding deployment types in Microsoft Foundry Models](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/deployment-types)
* [Model versions in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/foundry-models/concepts/model-versions)
* [Microsoft Foundry Models lifecycle and support policy](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirements)
* [Model retirement schedule](https://learn.microsoft.com/azure/foundry/openai/concepts/model-retirement-schedule)
* [Quota for Microsoft Foundry Models](https://learn.microsoft.com/azure/foundry/openai/how-to/quota)
* [Role-based access control in Microsoft Foundry](https://learn.microsoft.com/azure/foundry/concepts/rbac-foundry)
* [Network isolation for Foundry Agent Service](https://learn.microsoft.com/azure/foundry/agents/how-to/virtual-networks)
* [Trace Microsoft Agent Framework applications](https://learn.microsoft.com/azure/foundry/observability/how-to/trace-agent-framework)

### Azure application hosting

* [Azure Container Apps overview](https://learn.microsoft.com/azure/container-apps/overview)
* [Compare Azure Container Apps with other container options](https://learn.microsoft.com/azure/container-apps/compare-options)
* [Choose an Azure container service](https://learn.microsoft.com/azure/architecture/guide/choose-azure-container-service)
* [Azure Container Apps revisions](https://learn.microsoft.com/azure/container-apps/revisions)
* [Traffic splitting in Azure Container Apps](https://learn.microsoft.com/azure/container-apps/traffic-splitting)
* [Use a private endpoint with Azure Container Apps](https://learn.microsoft.com/azure/container-apps/how-to-use-private-endpoint)
* [Private endpoints and DNS for Azure Container Apps](https://learn.microsoft.com/azure/container-apps/private-endpoints-with-dns)
* [Use private endpoints for Azure App Service](https://learn.microsoft.com/azure/app-service/overview-private-endpoint)
* [Azure App Service deployment best practices](https://learn.microsoft.com/azure/app-service/deploy-best-practices)
* [What is Azure Kubernetes Service](https://learn.microsoft.com/azure/aks/what-is-aks)

### Testing evidence

* [Unit test agents with deterministic dependency mocks](https://learn.microsoft.com/microsoft-365/agents-sdk/unit-testing-agents-dotnet)

The testing reference demonstrates the general pattern used in this
recommendation: inject external dependencies and replace them with mocks so unit
tests remain deterministic and fast. The TokenNexus substitute list is derived
from NFR-007 and the product's own dependency boundaries rather than from a
single Azure hosting feature.

## Gaps and Clarifying Questions

The research is complete for architecture selection. These product and Azure
decisions remain open before provisioning:

* Which two models, providers, versions, deployment SKUs, aliases, and upgrade
  policies satisfy Q-004?
* Which Azure subscription, tenant, region, environments, capacity allocation,
  concurrency target, and operating budget satisfy Q-008?
* Does the selected model/provider combination support Microsoft Entra
  authentication and the required private-network path in the chosen region?
* Which reference domain and data classification determine whether public
  Entra-protected ingress is acceptable for MVP?
* Which evaluator, embedding model, cache store, telemetry store, and durable
  execution store will be frozen for measurement?
* What are the approved price source, budget thresholds, cache scope and expiry,
  content-filter settings, trace retention, and redaction rules?
* Who owns product, security, FinOps, support, incident response, and model
  retirement decisions?

No live subscription, quota, SKU, capacity, regional availability, pricing, or
network compatibility check was performed. Those checks depend on the unresolved
model and subscription decisions and must be completed immediately before
infrastructure planning and deployment.

## Recommended Next Research

* Select candidate economical and capable models, then compare current region,
  deployment type, price, quota, context, latency, and retirement information
* Run subscription-specific quota and regional-capacity checks for both models
* Confirm the end-to-end private-network and Entra authentication support matrix
  for the chosen models, cache, stores, and telemetry
* Produce a measured monthly cost envelope for development, evaluation, and
  production traffic assumptions
* Resolve the evaluator, embedding, cache, and durable-store choices against the
  selected domain and data classification

Status: Complete for deployment-option research and MVP topology selection;
blocked for resource-level design by the open model, subscription, region,
capacity, budget, and data-classification decisions.
