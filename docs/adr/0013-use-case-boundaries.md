# ADR 0013: Use-case boundaries and actor responsibilities (UML-ready)

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-05.
**Source:** `docs/context/02_actors_and_use_cases.md` [CONFIRMED names]; `docs/PHASE0_DISCOVERY.md` §2 (C4, C5, C10, C11)

## Context

Q1 (answered): there is no official UML, requirements document or rubric. UML diagrams will be produced **from** the approved design, so use-case boundaries must be clear now. The 9 use-case names and 6 actor names are confirmed and must not change. Three problems in the current concept:
- UC3 and UC4 have nearly identical names.
- UC1 says "Generate", which overlaps UC2–UC4.
- **Granting consent has no use case**; only revoking does.

## Options Considered

| Criterion | Keep the names and leave boundaries implicit | **Keep the names, define boundaries, add «include» relationships, and propose one included use case for consent grant** | Rename or merge use cases |
|---|---|---|---|
| Faithful to confirmed sources | Yes | **Yes (names unchanged)** | No |
| Viva-proof ("what's the difference between UC3 and UC4?") | No | **Yes** | Yes |
| UML-ready | No | **Yes** | Yes |

## Decision

| UC | Primary actor | Boundary (what it covers) | Ends when |
|---|---|---|---|
| UC1 Create and Generate a Localization Project | Localization Manager | Create and configure the project: target locale (ta-IN), audience profile, glossary, members, speakers. **"Generate" = starting the pipeline**, which «include»s UC2, then UC3 and UC4 as jobs. | Project configured and pipeline started |
| UC2 Upload and Analyze Source Video | Media Operator | Upload, ffprobe validation, audio extraction, transcription (local by default; external only with consent, CP0), scene and segment building, speaker assignment (with human correction) | Segments and scenes ready |
| UC3 Generate Context-Aware Localization Preview | Localization Manager (via «include» from UC1); Reviewer (via «include» from UC5) | **Script level:** Tamil draft per segment with rationale; hard checks and AI flags (ADR 0008). Reviewed as text. | Script draft with check results |
| UC4 Generate Localized Preview | Localization Manager (via «include» from UC1); Reviewer (via «include» from UC5) | **Media level:** speech synthesis with the resolved rendering mode (consent gate), timing fit, mixing, subtitles, preview video | Preview playable |
| UC5 Review and Regenerate a Scene | Reviewer / Linguist | Edit segments, resolve checks, acknowledge flags, accept a scene or request changes; regeneration re-runs UC3 and/or UC4 **for that scene only** | Scene accepted |
| UC6 Approve and Export Localization Package | Localization Manager | Approval of an immutable snapshot (all scenes accepted, no unresolved hard checks, consent active); export package with evidence manifest | Export available |
| UC7 Revoke Consent and Stop Identity | Speaker / Identity Owner | Revocation and its cascade (ADR 0006) | Cascade complete; local and Kaggle deletion confirmed or "deletion pending" |
| UC8 Administer Users, Providers and Policies | Administrator | Users, provider configuration, policies (provider chain order, free-quota warnings, retention, cloning allowed, separation of duties) | — |
| UC9 Inspect Quality, Audit and Evidence | Auditor / Faculty Evaluator | Read-only access to check results, reviews, approvals, audit chain verification, evidence manifests | — |

**Consent grant [CONFIRMED 2026-10-05]:** model **"Record Consent"** as an *included* use case (Identity Owner as actor), used by UC1 when a speaker is linked to an identity, and as the counterpart of UC7. This doesn't add a top-level use case. It makes visible a step that already has to exist.

**Actor naming:** the confirmed actor "Auditor / Faculty Evaluator" is kept as written. In the system it is the `AUDITOR` role (ADR 0011).

**Out of scope, listed as future scope (Q5):** lip-sync and face processing, replacing on-screen text, multiple target languages per project, real-time processing, external speakers outside the team.

## Consequences

- **+** UML use-case and activity diagrams can be drawn directly from this table.
- **+** UC3 and UC4 have a clear answer: text vs. media.
- **−** "Record Consent" adds one use case to the UML diagram (accepted 2026-10-05).
- **Viva in 2 minutes:** "UC3 produces the Tamil script and checks it. UC4 turns the approved script into audio and video. Reviewers work per scene in UC5, and the Manager approves a frozen snapshot in UC6."
