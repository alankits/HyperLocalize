# ADR 0001: Modular monolith with a separate worker process

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.1

## Context

HyperLocalize needs a web API for interactive work (projects, review, approval, consent) and long-running media and AI processing (transcription, translation, synthesis, rendering, export). Consent, approval and audit rules must stay consistent across these parts (CLAUDE.md §5). The team is a student team, and the design must be explainable in a viva (CLAUDE.md §6). The team is up to 4 students with intermediate Python, basic JavaScript/React and little DevOps experience, and about 5 months (Q2, answered 2026-10-05).

## Options Considered

| Criterion | Modular monolith + worker | Microservices | Serverless functions |
|---|---|---|---|
| Simplicity and explainability | High | Low | Medium |
| Consent and audit consistency | One DB transaction | Distributed consistency problem | Hard |
| Scalability | Enough for the demo; workers scale horizontally | High | High |
| Operations burden | Low | High | Medium; vendor lock-in |
| Long video jobs | Natural (worker process) | Natural | Awkward (execution time limits) |

## Decision

One codebase and one database, deployed as two process types: a **web process** that never blocks on long work, and **one worker process** that runs jobs (ADR 0003). The framework is Django (ADR 0009). Each module is a **Django app**:

| App | Owns | Main use cases |
|---|---|---|
| `accounts` | users, project memberships, roles | UC8 |
| `projects` | Project, AudienceProfile, GlossaryTerm, Video, media storage | UC1, UC2 |
| `localization` | Scene, Segment, SegmentTranslation, verification checks | UC2, UC3 |
| `rendering` | speech synthesis, timing fit, mixing, subtitles, previews | UC4 |
| `review` | Review, RegenerationRequest, Approval | UC5, UC6 |
| `identity` | IdentityOwner, Consent, VoiceProfile, **consent gate** | UC7 |
| `exports` | Export, evidence manifest | UC6 |
| `audit` | AuditRecord, chain verifier | UC9 |
| `pipeline` | Job table, worker command, provider interfaces and adapters (ADR 0005) | all |

Module rules:
- Apps call each other through plain service functions (`services.py`), not by writing each other's tables.
- Only the `identity` app decides consent (ADR 0006).
- Only the `audit` app writes audit records (ADR 0007).
- No Django signals are used for consent or audit, because hidden control flow is hard to defend in a viva.

## Consequences

- **+** Consent checks, state changes and audit writes can share one transaction.
- **+** One deployable unit; easy to run with Docker Compose and to explain.
- **−** Module boundaries depend on discipline, not network isolation. Mitigation: code review and the `services.py` convention. No extra tooling, because the team is small.
- **−** The single database is the scaling limit. That's acceptable for the demo scope and must be stated in the viva.
- **Viva in 2 minutes:** "One app, one database, one worker. Nine Django apps named after the use cases. Consent and audit each have exactly one owner."
