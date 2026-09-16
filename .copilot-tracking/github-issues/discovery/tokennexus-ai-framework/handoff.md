<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# GitHub Issue Operations Handoff

## Planning Files

* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/issue-analysis.md
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/issues-plan.md
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/planning-log.md
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/handoff.md

## Execution Guard

Review only. Do not execute until the repository, labels, milestone, hierarchy, and GitHub similarity assessment are confirmed. All operations remain unchecked.

## Summary

| Action | Count |
|--------|-------|
| Create | 35 |
| Update | 0 |
| Link | 27 |
| Close | 0 |
| Comment | 0 |
| No Change | 0 |

| Backlog Slice | Count |
|---------------|-------|
| P0 epics | 8 |
| P0 MVP stories | 24 |
| P1 deferred stories | 2 |
| P2 future stories | 1 |

## Issues

### Create Parent Epics

* [ ] {{TEMP-1}} feat(core): establish governed request orchestration
  Labels: Epic, P0-must-have, general-agent. Milestone: MVP Sprint.
* [ ] {{TEMP-2}} feat(economics): govern routing and request budgets
  Labels: Epic, P0-must-have, billing-agent. Milestone: MVP Sprint.
* [ ] {{TEMP-3}} feat(quality): control cache, evaluation, and escalation
  Labels: Epic, P0-must-have, technical-agent. Milestone: MVP Sprint.
* [ ] {{TEMP-4}} feat(security): enforce protected specialist and tool actions
  Labels: Epic, P0-must-have, technical-agent. Milestone: MVP Sprint.
* [ ] {{TEMP-5}} feat(client): deliver the request workspace and recoverable sessions
  Labels: Epic, P0-must-have, general-agent. Milestone: MVP Sprint.
* [ ] {{TEMP-6}} feat(evidence): provide economics observability and control evidence
  Labels: Epic, P0-must-have, observability. Milestone: MVP Sprint.
* [ ] {{TEMP-7}} feat(platform): deploy the Azure MVP runtime
  Labels: Epic, P0-must-have, infrastructure. Milestone: MVP Sprint.
* [ ] {{TEMP-8}} test(mvp): prove release acceptance and quality gates
  Labels: Epic, P0-must-have, general-agent. Milestone: MVP Sprint.

### Create P0 MVP Stories

* [ ] {{TEMP-9}} feat(api): publish versioned request and result contracts
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-1}}.
* [ ] {{TEMP-10}} feat(core): implement deterministic coordinator and idempotency journal
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-1}}.
* [ ] {{TEMP-11}} feat(models): add provider-neutral model adapters and deterministic substitutes
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-1}}.
* [ ] {{TEMP-12}} feat(routing): select eligible models with versioned policy
  Labels: User Story, P0-must-have, P0, billing-agent. Parent: {{TEMP-2}}.
* [ ] {{TEMP-13}} feat(budget): estimate cost and enforce request budget actions
  Labels: User Story, P0-must-have, P0, billing-agent. Parent: {{TEMP-2}}.
* [ ] {{TEMP-14}} feat(policy): administer confirmed versioned policy changes
  Labels: User Story, P0-must-have, P0, billing-agent. Parent: {{TEMP-2}}.
* [ ] {{TEMP-15}} feat(cache): implement scoped semantic response reuse
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-3}}.
* [ ] {{TEMP-16}} feat(quality): evaluate every non-cached response
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-3}}.
* [ ] {{TEMP-17}} feat(escalation): retry low-quality output once when eligible
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-3}}.
* [ ] {{TEMP-19}} feat(auth): enforce server-side roles for protected actions
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-4}}.
* [ ] {{TEMP-20}} feat(tools): mediate bounded specialist tool calls
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-4}}.
* [ ] {{TEMP-21}} feat(privacy): externalize secrets and minimize retained content
  Labels: User Story, P0-must-have, P0, technical-agent. Parent: {{TEMP-4}}.
* [ ] {{TEMP-22}} feat(client): build the usable request workspace
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-5}}.
* [ ] {{TEMP-23}} feat(session): preserve non-sensitive work across interruptions
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-5}}.
* [ ] {{TEMP-24}} feat(explainability): present safe decision summaries
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-5}}.
* [ ] {{TEMP-26}} feat(journal): persist immutable execution economics records
  Labels: User Story, P0-must-have, P0, observability. Parent: {{TEMP-6}}.
* [ ] {{TEMP-27}} feat(telemetry): export metadata-only OpenTelemetry traces and metrics
  Labels: User Story, P0-must-have, P0, observability. Parent: {{TEMP-6}}.
* [ ] {{TEMP-28}} feat(reporting): compare MVP economics with the all-frontier baseline
  Labels: User Story, P0-must-have, P0, observability, billing-agent. Parent: {{TEMP-6}}.
* [ ] {{TEMP-29}} feat(compliance): assemble the MVP evidence catalog
  Labels: User Story, P0-must-have, P0, observability. Parent: {{TEMP-6}}.
* [ ] {{TEMP-30}} feat(azure): deploy the API and two Foundry model aliases
  Labels: User Story, P0-must-have, P0, infrastructure. Parent: {{TEMP-7}}.
* [ ] {{TEMP-31}} feat(identity): configure managed identity, RBAC, and versioned settings
  Labels: User Story, P0-must-have, P0, infrastructure. Parent: {{TEMP-7}}.
* [ ] {{TEMP-32}} feat(operations): validate rollback, capacity, and controlled failure
  Labels: User Story, P0-must-have, P0, infrastructure. Parent: {{TEMP-7}}.
* [ ] {{TEMP-33}} test(core): create deterministic contract and policy test harness
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-8}}.
* [ ] {{TEMP-34}} test(mvp): automate the eight end-to-end acceptance scenarios
  Labels: User Story, P0-must-have, P0, general-agent. Parent: {{TEMP-8}}.

### Create Deferred Stories

* [ ] {{TEMP-18}} feat(runtime): return controlled degraded outcomes
  Labels: User Story, P1-should-have, technical-agent. Parent: {{TEMP-3}}. Milestone: none.
* [ ] {{TEMP-35}} test(quality): verify performance, accessibility, and release gates
  Labels: User Story, P1-should-have, general-agent. Parent: {{TEMP-8}}. Milestone: none.
* [ ] {{TEMP-25}} feat(feedback): record explicit user ratings
  Labels: User Story, P2-future, general-agent. Parent: {{TEMP-5}}. Milestone: none.

### Link Sub-Issues

* [ ] Link {{TEMP-9}} as a sub-issue of {{TEMP-1}}
* [ ] Link {{TEMP-10}} as a sub-issue of {{TEMP-1}}
* [ ] Link {{TEMP-11}} as a sub-issue of {{TEMP-1}}
* [ ] Link {{TEMP-12}} as a sub-issue of {{TEMP-2}}
* [ ] Link {{TEMP-13}} as a sub-issue of {{TEMP-2}}
* [ ] Link {{TEMP-14}} as a sub-issue of {{TEMP-2}}
* [ ] Link {{TEMP-15}} as a sub-issue of {{TEMP-3}}
* [ ] Link {{TEMP-16}} as a sub-issue of {{TEMP-3}}
* [ ] Link {{TEMP-17}} as a sub-issue of {{TEMP-3}}
* [ ] Link {{TEMP-18}} as a sub-issue of {{TEMP-3}}
* [ ] Link {{TEMP-19}} as a sub-issue of {{TEMP-4}}
* [ ] Link {{TEMP-20}} as a sub-issue of {{TEMP-4}}
* [ ] Link {{TEMP-21}} as a sub-issue of {{TEMP-4}}
* [ ] Link {{TEMP-22}} as a sub-issue of {{TEMP-5}}
* [ ] Link {{TEMP-23}} as a sub-issue of {{TEMP-5}}
* [ ] Link {{TEMP-24}} as a sub-issue of {{TEMP-5}}
* [ ] Link {{TEMP-25}} as a sub-issue of {{TEMP-5}}
* [ ] Link {{TEMP-26}} as a sub-issue of {{TEMP-6}}
* [ ] Link {{TEMP-27}} as a sub-issue of {{TEMP-6}}
* [ ] Link {{TEMP-28}} as a sub-issue of {{TEMP-6}}
* [ ] Link {{TEMP-29}} as a sub-issue of {{TEMP-6}}
* [ ] Link {{TEMP-30}} as a sub-issue of {{TEMP-7}}
* [ ] Link {{TEMP-31}} as a sub-issue of {{TEMP-7}}
* [ ] Link {{TEMP-32}} as a sub-issue of {{TEMP-7}}
* [ ] Link {{TEMP-33}} as a sub-issue of {{TEMP-8}}
* [ ] Link {{TEMP-34}} as a sub-issue of {{TEMP-8}}
* [ ] Link {{TEMP-35}} as a sub-issue of {{TEMP-8}}

## Follow-Up Attention

* Verify repository metadata and perform similarity assessment before creating anything.
* Validate that all requested labels exist or approve their creation.
* Confirm the proposed MVP milestone.
* Confirm policy administration and rollback/capacity as P0 because they satisfy a required acceptance scenario and the release-ready gate.
* Resolve the PRD's nine open product decisions before production-value stories can close.

<!-- markdown-table-prettify-ignore-end -->