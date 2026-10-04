# ADR 0001: Modular monolith with a separate worker process

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.1

## Context

HyperLocalize needs a web API for interactive work (projects, review, approval, consent) and long-running media and AI processing (transcription, translation, synthesis, rendering, export). Consent, approval and audit rules must stay consistent across these parts (CLAUDE.md §5). The team is a student team, and the design must be explainable in a viva (CLAUDE.md §6). Team size and skills are [UNKNOWN] (Q2).

## Options Considered

| Criterion | Modular monolith + worker | Microservices | Serverless functions |
|---|---|---|---|
| Simplicity and explainability | High | Low | Medium |
| Consent and audit consistency | One DB transaction | Distributed consistency problem | Hard |
| Scalability | Enough for the demo; workers scale horizontally | High | High |
| Operations burden | Low | High | Medium; vendor lock-in |
| Long video jobs | Natural (worker process) | Natural | Awkward (execution time limits) |

## Decision

One codebase and one database, split into domain modules (`accounts`, `projects`, `media`, `analysis`, `localization`, `rendering`, `review`, `identity`, `exports`, `audit`, `providers`, `jobs`). It is deployed as two process types: an **API process** that never blocks on long work, and one or more **worker processes** that run jobs (ADR 0003).

Module rules:
- Modules call each other through explicit service functions, not by reaching into each other's tables.
- Consent decisions are made only by the `identity` module's consent gate (ADR 0006).
- Audit records are written only through the `audit` module (ADR 0007).

## Consequences

- **+** Consent checks, state changes and audit writes can share one transaction.
- **+** One deployable unit; easy to run with Docker Compose and to explain.
- **−** Module boundaries depend on discipline, not network isolation. Mitigation: code review, plus import-boundary checks if a tool for the chosen language makes that cheap.
- **−** The single database is the scaling limit. That's acceptable for the demo scope and must be stated in the viva.
- Framework choice (Django vs. FastAPI) is a separate, pending ADR (group B2). This ADR is framework-neutral.
