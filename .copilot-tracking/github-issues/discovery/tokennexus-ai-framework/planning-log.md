<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Discovery - Issue Planning Log

* **Repository**: TokenNexus-AI/TokenNexus-AI (provisional)
* **Proposed Milestone**: MVP Sprint
* **Autonomy**: Manual, planning only
* **Previous Phase**: Phase 2 - Plan Issues
* **Current Phase**: Phase 3 - Assemble Handoff (Complete)

## Status

35/35 issues planned, 27/27 parent-child relationships planned, 0 GitHub searches run, and 0 GitHub mutations made.

**Summary**: Artifact-driven discovery is complete for review. Eight epics group 27 user stories. Twenty-four stories are P0 and form the proposed MVP sprint; two are P1 and one is P2. Similarity search, repository metadata validation, label validation, milestone validation, issue creation, and sub-issue linking remain pending by explicit user request.

## Phase History

| Phase | Status | Outcome |
|-------|--------|---------|
| Phase 1 - Discover Issues | Complete with external search deferred | Parsed the PRD and architecture research; extracted 35 candidates and mapped all Must requirements and acceptance scenarios |
| Phase 2 - Plan Issues | Complete | Produced GitHub-ready epic and story bodies with Given/When/Then criteria, requested labels, priorities, and hierarchy |
| Phase 3 - Assemble Handoff | Complete | Produced review handoff with 35 Create and 27 Link operations, all unchecked and unexecuted |

## Discovered Artifacts and Related Files

* AT001 docs/prds/tokennexus-ai-framework-prd.md - Complete - Primary requirements source
* AT002 .copilot-tracking/research/2026-09-15/tokennexus-ai-framework-implementation-research.md - Complete - Architecture synthesis
* AT003 .copilot-tracking/research/subagents/2026-09-15/domain-contracts-reason-codes-research.md - Complete - Contract and reason-code decisions
* AT004 .copilot-tracking/research/subagents/2026-09-15/policy-evaluator-cache-defaults-research.md - Complete - Policy, evaluator, cache, memory, and bounded-runtime defaults
* AT005 .copilot-tracking/research/subagents/2026-09-15/bounded-agent-tool-threat-model-research.md - Complete - Capability facade and protected-tool controls

## Issue Progress

| Range | Kind | Priority | Domain Focus | Status |
|-------|------|----------|--------------|--------|
| IS001-IS008 | Epic | P0-must-have | All requested domains | Complete |
| IS009-IS013 | User Story | P0 | Contracts, coordination, models, routing, budget | Complete |
| IS014 | User Story | P0 | Policy administration required by acceptance scenario 7 | Complete |
| IS015-IS017 | User Story | P0 | Cache, quality, escalation | Complete |
| IS018 | User Story | P1 | Controlled degradation | Complete |
| IS019-IS024 | User Story | P0 | Authorization, tools, privacy, client, session, explanations | Complete |
| IS025 | User Story | P2 | Feedback | Complete |
| IS026-IS031 | User Story | P0 | Journal, telemetry, reporting, evidence, Azure runtime, identity | Complete |
| IS032 | User Story | P0 | Rollback and capacity required by the release-ready gate | Complete |
| IS033-IS034 | User Story | P0 | Deterministic and end-to-end validation | Complete |
| IS035 | User Story | P1 | Performance and accessibility | Complete |

## Requirement Coverage

* All Must functional requirements are assigned to at least one P0 story.
* All Must non-functional requirements are assigned to at least one P0 story.
* All eight required acceptance scenarios are owned by the P0 end-to-end suite and their implementation stories.
* All seven product goals have an implementation or reporting path.
* CR-001 through CR-008 are owned by the P0 evidence catalog and their contributing stories.

## Discovered GitHub Issues

None. GitHub API calls were prohibited for this planning run.

## Deferred Search Protocol

Before execution, authenticate against the confirmed repository and search open and closed issues using these ordered keyword groups:

1. `"governed orchestration" OR "request coordinator" OR idempotency`
2. `"policy routing" OR "model routing" OR "budget action"`
3. `"semantic cache" OR "quality evaluator" OR escalation`
4. `"capability facade" OR "protected tool" OR "server-side authorization"`
5. `"request workspace" OR "session recovery" OR "decision summary"`
6. `"execution record" OR OpenTelemetry OR "baseline comparison"`
7. `"Container Apps" OR "Foundry model" OR "managed identity"`
8. `"acceptance scenarios" OR "deterministic substitutes" OR accessibility`

Hydrate plausible matches, compare title, body, labels, milestone, and type, then classify each planned issue as Match, Similar, Distinct, or Uncertain. Do not create any issue until this similarity gate is complete.

## Milestone Discovery

Milestone strategy could not be inspected without GitHub access. `MVP Sprint` is a proposed working milestone, not an existing verified milestone. P0 stories are the intended members; P1 and P2 stories have no proposed milestone.

## Review Decisions

* Confirm the actual GitHub `owner/repo`.
* Confirm or replace the proposed `MVP Sprint` milestone.
* Confirm label names and capitalization, including both `P0-must-have` and `P0` on MVP stories.
* Confirm eight parent epics and the 27 child-story grouping.
* Confirm that policy administration and rollback/capacity remain P0 because they are required by acceptance scenario 7 and the release-ready gate.

## Resume Context

Working files:

* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/issue-analysis.md - Candidate inventory, architecture constraints, label plan, and coverage matrix
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/issues-plan.md - Source of truth for issue bodies, fields, and hierarchy
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/planning-log.md - Workflow state and deferred search criteria
* .copilot-tracking/github-issues/discovery/tokennexus-ai-framework/handoff.md - Review queue for future execution

<!-- markdown-table-prettify-ignore-end -->