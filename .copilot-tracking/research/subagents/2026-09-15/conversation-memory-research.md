---
title: Conversation Memory Research
description: Evidence-based evaluation of conversation memory strategies for TokenNexus-AI-Framework
ms.date: 2026-09-15
ms.topic: concept
---

## Research Scope

### Questions

* How should request-scoped state, session-level memory, persistent memory, summaries, retrieval stores, and provider-managed threads be divided?
* How should data classification, isolation, retention, consent, deletion, encryption, redaction, caching, injection defense, cost, concurrency, versioning, and tests shape the design?
* Which MVP approach best matches raw prompt persistence off by default and scoped semantic caching?

## Repository Evidence

The product requirements constrain memory more strongly than they require it:

* The product principle in docs/prds/tokennexus-ai-framework-prd.md:134-139 says raw prompt and response content should not be persisted by default.
* FR-005 in docs/prds/tokennexus-ai-framework-prd.md:174 requires scoped semantic reuse while stale, sensitive, and freshness-critical requests bypass the cache.
* FR-009 in docs/prds/tokennexus-ai-framework-prd.md:178 requires economics and outcome telemetry, but does not require conversation text.
* FR-014 in docs/prds/tokennexus-ai-framework-prd.md:183 requires prompt capture to default to off or redacted and requires traces and logs to exclude credentials.
* FR-017 in docs/prds/tokennexus-ai-framework-prd.md:186 requires session reuse and recovery of non-sensitive work. This is an authentication and user-experience requirement, not a requirement for durable transcript retention.
* FR-020 in docs/prds/tokennexus-ai-framework-prd.md:189 treats untrusted content as data and constrains tool use. Stored summaries and retrieved memories must preserve the same trust boundary.
* NFR-002 in docs/prds/tokennexus-ai-framework-prd.md:196 requires raw content persistence to be off by default and any enabled capture to support redaction and configurable retention.
* NFR-007 in docs/prds/tokennexus-ai-framework-prd.md:201 requires deterministic substitutes for model, evaluator, cache, pricing, and tool integrations.
* The execution record in docs/prds/tokennexus-ai-framework-prd.md:210-228 can be satisfied with identifiers, classifications, reason codes, token counts, costs, timing, quality, cache metadata, and attempt links. Raw conversation text is not a required field.
* R-004 in docs/prds/tokennexus-ai-framework-prd.md:266 classifies stale, sensitive, or cross-scope cache results as a critical risk. Its required controls are scoped keys, expiration, sensitivity bypass, and isolation tests.
* CR-004 in docs/prds/tokennexus-ai-framework-prd.md:285 requires evidence for redaction, bypass, isolation, and expiration.

The BRD reinforces this boundary:

* docs/brds/tokennexus-ai-framework-brd.md:91 requires cache partitioning, expiration, and bypass for sensitive or freshness-critical requests.
* docs/brds/tokennexus-ai-framework-brd.md:148 distinguishes session reuse in the MVP from future enterprise identity lifecycle controls.
* docs/brds/tokennexus-ai-framework-brd.md:153 limits the MVP cache to semantic lookup, scoped keys, expiration, and sensitivity bypass. Distributed caching, legal hold, and enterprise retention administration are deferred.
* BR-014 and NFR-002 in docs/brds/tokennexus-ai-framework-brd.md:187 and 219 prohibit default raw-content retention.

These requirements support a metadata-first design. They do not justify persistent profile memory, durable transcripts, or provider-owned conversation threads in the MVP.

## Authoritative External Evidence

### Provider-managed state

The Azure OpenAI Responses API supports both stateless requests and stateful continuation. The API can store response state for later retrieval and chaining, and stored responses can be deleted. Setting `store` to `false` avoids application-requested response storage and is the closest fit for the repository's default-off persistence rule. Stateful continuation is convenient, but it creates a second lifecycle domain whose retention, deletion, regional behavior, and provider identifiers must be governed alongside the application's own stores.

Design consequence: use stateless provider calls for the MVP. If provider-managed state is enabled later, register each provider object against the owning tenant, user, purpose, expiration, and deletion status. Application deletion must fan out to the provider and retain only a non-content deletion receipt.

### Time-limited application state

Azure Cosmos DB supports a default TTL at container level and an item-level TTL override. After an item expires, it is no longer returned by queries and is deleted by a background process. This supports bounded session state, but TTL is an expiry mechanism rather than proof of immediate physical erasure. A deletion workflow still needs explicit delete operations, verification, and evidence when a user or administrator requests deletion before expiry.

Cosmos DB also uses `_etag` values for optimistic concurrency. Conditional writes with `If-Match` reject stale updates, which can prevent concurrent turns from silently overwriting a session summary. Transactional guarantees are scoped to a logical partition, so the partition and session-key design must keep records that require atomic updates together.

### Isolation

Microsoft's multitenancy guidance distinguishes shared logical isolation from dedicated physical isolation. A tenant identifier in the partition key supports efficient logical separation, but the application must include and authorize the tenant context on every operation. A partition key is not an authorization boundary. Higher-risk tenants can move to dedicated containers, databases, accounts, or deployment stamps when physical isolation is required.

Design consequence: derive tenant and user identity from authenticated server context rather than request text. Use a composite logical scope such as tenant, application/use case, user or group, and session. Reject reads or writes whose authenticated scope does not match the record scope.

### Semantic cache separation

Azure API Management semantic-cache policies expose explicit lookup and store stages, duration controls, and variation dimensions. This supports a separate cache lifecycle, but a semantic cache remains a response-reuse system rather than conversation memory. Cache entries should be keyed by policy-relevant scope and embedding/model versions, and should never be silently promoted into a user profile or transcript.

Design consequence: keep cache records in a distinct store or container with separate access policy, schema, TTL, metrics, and deletion path. Sensitive, personalized, freshness-critical, tool-bearing, or policy-disallowed requests must bypass both lookup and store.

### Telemetry minimization

OpenTelemetry's GenAI semantic conventions define metadata such as system, operation, model, token usage, and conversation identifiers. Input and output messages contain sensitive content and are opt-in rather than baseline telemetry. OpenTelemetry also recommends filtering or redacting sensitive data before export.

Design consequence: emit request and trace identifiers, not prompts, responses, summaries, retrieval chunks, tool payloads, cache values, or memory records. Any diagnostic content capture must be a separate, time-bound, authorized mode with visible purpose, redaction, sampling, and deletion controls.

### Stored-content injection

OWASP treats prompt injection as an architectural risk that cannot be solved by prompt wording alone. Retrieved documents and stored memories are untrusted inputs. They can contain direct or indirect instructions that alter model behavior or tool calls.

Design consequence: label memory provenance and trust level, treat summaries and retrieved records as quoted data, keep system instructions separate, constrain tools independently of model output, and never allow recalled content to grant permissions or override policy.

### Privacy governance

The NIST Privacy Framework provides a risk-management structure for identifying data processing, governing it, controlling it, communicating about it, and protecting it. GDPR principles apply when personal data is in scope, including purpose limitation, data minimization, storage limitation, privacy by default, and erasure. These sources do not prescribe a specific memory database; they require the product to make purpose, retention, access, and deletion enforceable and reviewable.

## Alternatives

| Approach | Lifecycle and content | Benefits | Main risks and costs | MVP decision |
| --- | --- | --- | --- | --- |
| Request-scoped state | In-process normalized request, policy decision, model attempts, and result; discarded after completion | Lowest privacy burden, deterministic, simple deletion, no cross-request leakage | No conversational continuity across requests | Required foundation |
| Ephemeral session state | Application-owned, non-sensitive working state with inactivity and absolute TTL | Supports session recovery and short conversational continuity while preserving lifecycle control | Concurrent updates, scope mistakes, summary drift, residual personal data | Recommended with strict bounds |
| Persistent user or application memory | Durable preferences, facts, and history across sessions | Better personalization and fewer repeated inputs | Consent, correction, provenance, staleness, deletion fan-out, poisoning, tenant leakage, higher governance cost | Exclude from MVP |
| Rolling summaries | Model-generated compression of prior turns | Lower token cost than replaying transcripts | Lossy facts, embedded injection, hallucinated commitments, version drift, summary itself remains sensitive | Optional only inside ephemeral session state |
| Retrieval store | Searchable chunks, embeddings, and provenance records | Selective context and scalable knowledge access | Data duplication, deletion of vectors and source copies, ranking attacks, stale content, embedding-version migration | Use only for approved knowledge, not personal conversation memory |
| Semantic response cache | Scoped mapping from eligible meaning to reusable result | Directly satisfies FR-005 and avoids model calls | Cross-scope leakage, stale or personalized output, similarity false positives | Required, but separate from memory |
| Provider-managed responses or threads | Conversation objects retained by the model provider | Convenient continuation and reduced application orchestration | Additional retention/deletion domain, provider coupling, reduced deterministic control, hidden lifecycle assumptions | Disable for MVP with `store=false` |
| Durable transcript store | Full prompt/response history | Maximum replay and audit detail | Direct conflict with default-off persistence, highest breach impact, token replay cost, difficult deletion and legal obligations | Reject for MVP |

The critical distinction is purpose. Session state supports an active interaction. Persistent memory personalizes later interactions. Retrieval supplies approved knowledge. Semantic caching reuses an eligible answer. Telemetry explains system behavior. Authentication sessions preserve identity. Provider threads continue provider state. Combining these concerns in one record or store produces ambiguous retention, access, and deletion behavior.

## Recommended MVP

### Decision

Use application-owned ephemeral memory with stateless provider invocation:

1. Keep request-scoped execution state in process and discard content after the final response.
2. Store only the minimum non-sensitive session working state needed for FR-017 recovery. Prefer structured fields over transcript text.
3. Call the Responses API with `store=false`. Send only the bounded context needed for the current attempt.
4. Keep semantic-cache entries in a separate lifecycle and authorization domain.
5. Persist metadata-only execution records for FR-009 and compliance evidence.
6. Exclude durable transcripts, cross-session profile memory, and provider-managed threads from MVP scope.

### Memory object

An ephemeral session record should contain no raw prompt or response fields by default. A minimal schema is:

* `session_id`: random opaque identifier
* `tenant_id`, `application_id`, `user_scope_id`: server-derived scope
* `classification`: highest classification permitted in the record
* `purpose`: fixed enum such as `active_request_recovery`
* `state_version` and `_etag`: schema and concurrency controls
* `policy_version`: policy used to admit and transform state
* `created_at`, `last_accessed_at`, `expires_at`: absolute and inactivity limits
* `working_constraints`: non-sensitive quality, latency, and budget selections
* `public_decision_state`: safe model alias, reason codes, and bounded status
* `summary`: absent by default; if enabled, a redacted structured summary with provenance and summary-policy version
* `deletion_status`: active, deletion-pending, or deleted receipt

Do not store authorization claims, secrets, raw tool arguments, retrieved chunks, hidden instructions, model chain-of-thought, full prompts, or full responses.

### Classification and admission

Classify before memory or cache writes:

| Class | Example | Session state | Semantic cache | Telemetry content |
| --- | --- | --- | --- | --- |
| Public | Approved public question | Structured state allowed | Allowed when freshness permits | Metadata only |
| Internal | Business context without personal or secret data | Redacted structured state allowed | Scope-restricted | Metadata only |
| Sensitive or personal | Personal, confidential, regulated, or customer data | Do not retain in MVP | Bypass lookup and store | Metadata only |
| Secret or credential | Keys, tokens, passwords, hidden instructions | Reject or redact immediately | Always bypass | Never record |

The admission decision must be deterministic and versioned. Unknown classification fails toward less retention: process the request when policy permits, but do not write memory or cache content.

### Isolation and authorization

Use an authenticated server-side scope for every read, update, query, and deletion. Partition by tenant first, then include application/use-case and user or approved group scope in the key. Do not accept these scope values from model output or untrusted request content. Use dedicated physical storage for a tenant when contractual or regulatory isolation cannot be met by an application-enforced shared store.

Access roles should be purpose-specific:

* The runtime identity can read and update only active records in its own scope.
* Cache administration cannot read session summaries.
* Telemetry readers cannot read memory or cache values.
* Support access is denied by default and requires a time-bound audited workflow.
* Deletion workers can locate and delete records but should not export their content.

Use platform encryption at rest and TLS in transit. Where threat or contractual requirements demand separation from platform operators, add customer-managed keys, but do not treat encryption as a substitute for minimization or authorization.

### Retention, consent, and deletion

Set both inactivity and absolute expiration. Exact durations remain a product and privacy decision; for the hackathon, use a short documented default and make it configuration rather than code. Do not refresh the absolute deadline on access.

Ephemeral active-session state is justified by the immediate service purpose and should be visible to the user as temporary. Any future cross-session memory requires an explicit product decision covering purpose, opt-in or other lawful basis, view/correct/delete controls, retention, and a separate privacy review.

Deletion must cover every derived representation:

1. Resolve records from authenticated tenant, user, application, and session scope.
2. Delete session state and any separately authorized summaries.
3. Evict related semantic-cache entries when their keys include user-derived content.
4. Delete retrieval chunks and embeddings if future personal-memory retrieval exists.
5. Delete provider responses or threads if that future feature is enabled.
6. Retain only a content-free audit receipt containing operation ID, scope hash, timestamp, systems attempted, and outcome.
7. Retry partial failures idempotently and surface unresolved systems for operations review.

### Concurrency and versioning

Use compare-and-swap updates with ETags. Each turn reads the current record, computes a new structured state, and writes with `If-Match`. On conflict, reload and deterministically merge commutative metadata or ask the caller to retry. Never silently apply last-write-wins to summaries or user-visible constraints.

Version all behavior that changes interpretation:

* Memory schema
* Classification and redaction policy
* Summary prompt and model, when summaries are enabled
* Cache key, embedding model, similarity threshold, and response policy
* Retrieval chunking and ranking policy
* Provider-state adapter

Records with unsupported versions must be ignored, migrated through an audited job, or deleted. They must not be reinterpreted opportunistically at read time.

### Token economics

Request state has no replay cost. Bounded summaries reduce input tokens compared with full-history replay, but summarization itself incurs model cost and quality risk. Persistent vector memory adds embedding, storage, retrieval, reranking, and deletion-index costs. Provider threads can simplify client payloads but do not remove model processing costs or lifecycle obligations.

For the MVP, cap session context by structured field count and estimated tokens. Apply a deterministic truncation order that preserves current instructions and mandatory evidence. When the cap is reached, discard optional old state rather than creating an unbounded recursive summary.

### Injection defenses

* Store provenance, author, creation time, and trust class with every summary or retrieval record.
* Delimit recalled content as untrusted data and never concatenate it into system instructions.
* Run classification and redaction before writes and again before context assembly.
* Allowlist memory fields that may influence routing; model-generated text cannot change policy, budget, identity, or tool permissions.
* Apply tool authorization and argument validation after model output, independently of memory content.
* Quarantine records that trigger injection or secret-detection rules and omit them from future context.

## Deterministic Test Strategy

Use in-memory adapters with a fake clock, deterministic classifier, fixed summarizer, deterministic embedding vectors, fake provider client, and controllable ETag store. Freeze schema, policy, cache, embedding, and summarizer versions in the test manifest.

| Test | Setup and assertion |
| --- | --- |
| Default persistence | Submit prompt and response canaries; assert neither appears in session store, cache-ineligible paths, logs, spans, or provider calls after completion; assert `store=false` |
| Allowed recovery | Interrupt a routine request; assert only allowlisted non-sensitive fields restore under the same authenticated scope |
| Sensitive bypass | Mark or detect sensitive and freshness-critical cases; assert no session summary or semantic-cache lookup/store occurs |
| Scope isolation | Generate tenant, application, user, and session collisions; assert every cross-scope read, query, update, and deletion is denied |
| TTL behavior | Advance the fake clock through inactivity and absolute deadlines; assert expired state is unavailable and deletion evidence is emitted |
| Explicit deletion | Seed session, cache, retrieval, and provider-adapter records; assert idempotent fan-out deletes every representation and retains only a content-free receipt |
| Concurrency | Run two writes against one ETag; assert one succeeds, one conflicts, and no state is silently lost |
| Version mismatch | Seed unsupported schema, redaction, summary, cache, and embedding versions; assert bypass, controlled migration, or deletion rather than reinterpretation |
| Summary fidelity | Feed fixed turns to a deterministic summarizer; assert mandatory constraints and provenance survive while secrets and disallowed fields do not |
| Injection resistance | Seed direct and indirect instructions in summaries and retrieval chunks; assert policy, identity, budget, and tool permissions remain unchanged |
| Cache separation | Delete or expire session state; assert unrelated shared cache behavior follows its own policy; assert user-derived cache entries are evicted when required |
| Telemetry minimization | Scan exported spans, logs, metrics, and decision records for content canaries, secrets, tool payloads, and memory values; expect zero matches |
| Token bounds | Seed oversized state; assert deterministic truncation, maximum context estimate, and preservation of mandatory context |
| Repeatability | Run the complete fixture set twice; assert identical memory admission, cache decisions, provider requests, public reason codes, and deletion outcomes |

Production-oriented tests should additionally validate Cosmos DB ETag conflicts, item TTL, partition-scoped access, managed-identity permissions, backup behavior, and deletion across all configured regions and replicas.

## Gaps and Clarifying Questions

The research recommendation is complete, but implementation values remain open:

* What exact inactivity and absolute TTLs are acceptable for the reference client?
* Which data classifications may appear in the demonstration, and who owns classification policy?
* Is even a redacted rolling summary necessary for the five core scenarios, or can structured constraints alone satisfy recovery?
* Which tenant-isolation tier is required for the hackathon and for a future production service?
* What user-facing notice and control are required for temporary session state?
* Which deletion completion target and evidence retention period will operations support?
* Will semantic caching run in the application, Azure API Management, or another store, and which identity dimensions must vary the key?
* Are provider-managed responses prohibited by policy, or merely disabled by default pending a privacy and operations review?

These questions affect configuration and future scope. None blocks the MVP architecture: stateless provider calls, metadata-only telemetry, separate scoped cache, and short-lived application-owned session state.

## References

### Workspace

* docs/prds/tokennexus-ai-framework-prd.md:134-139, 174, 178, 183, 186, 189, 196-201, 210-228, 266, 285
* docs/brds/tokennexus-ai-framework-brd.md:91, 148, 153, 178, 187, 219, 238-239

### External

* [Azure OpenAI Responses API](https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/responses)
* [Data, privacy, and security for Azure OpenAI Service](https://learn.microsoft.com/en-us/legal/cognitive-services/openai/data-privacy)
* [Configure time to live in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/how-to-time-to-live)
* [Transactions and optimistic concurrency control in Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency)
* [Multitenancy and Azure Cosmos DB](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/service/cosmos-db)
* [Architectural approaches for storage and data in multitenant solutions](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/approaches/storage-data)
* [Enable semantic caching for Azure OpenAI APIs](https://learn.microsoft.com/en-us/azure/api-management/azure-openai-enable-semantic-caching)
* [Azure API Management LLM semantic cache lookup policy](https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-lookup-policy)
* [Azure API Management LLM semantic cache store policy](https://learn.microsoft.com/en-us/azure/api-management/llm-semantic-cache-store-policy)
* [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai)
* [OpenTelemetry GenAI spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md)
* [OpenTelemetry handling sensitive data](https://opentelemetry.io/docs/security/handling-sensitive-data/)
* [OWASP LLM01: Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
* [NIST Privacy Framework](https://www.nist.gov/privacy-framework/privacy-framework)
* [GDPR Article 5: Principles relating to processing of personal data](https://eur-lex.europa.eu/eli/reg/2016/679/art_5/oj)
* [GDPR Article 17: Right to erasure](https://eur-lex.europa.eu/eli/reg/2016/679/art_17/oj)
* [GDPR Article 25: Data protection by design and by default](https://eur-lex.europa.eu/eli/reg/2016/679/art_25/oj)
