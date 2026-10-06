# HyperLocalize: Canonical Product Definition

| | |
|---|---|
| **Status** | Canonical product boundary, set by the user 2026-10-06 |
| **Applies to** | Every implementation, UML diagram, PPT, report and viva explanation |
| **Sources** | `docs/context/01`–`05`; `CLAUDE.md`; accepted ADRs 0001–0014; provisional and proposed ADRs 0015–0020; `docs/SPIKE_PLAN.md`; the Q answers in `docs/PHASE0_DISCOVERY.md` §11; the user's definition (2026-10-06) |

**Labels:**
- **[CONFIRMED]** means one of: stated in `docs/context/` or `CLAUDE.md`; decided by the user; or an accepted ADR. An accepted ADR is a *design or implementation decision*, not a built feature.
- **[PROPOSED]** means suggested but not finalized.
- **[INFERRED]** means a reasonable interpretation of confirmed material.
- **[UNKNOWN]** means not established yet.

**Layers** (never mix them):
- **Product requirement:** a core HyperLocalize capability.
- **MVP:** the scope for the first demonstrable build.
- **Spike decision:** a temporary decision used to evaluate candidate components.
- **Demo scenario:** the current health/ORS, English → Tamil test case.
- **Implementation choice:** the current technical architecture.
- **Proposed:** a future idea or an unfinalized design.

---

## 1. The product

HyperLocalize is a **context-aware, identity-preserving video localization system** [CONFIRMED]. It adapts source video content for a target audience while preserving the intended meaning [CONFIRMED].

It is a **general, controlled localization workflow**. It is not a single-domain or single-language tool [CONFIRMED].

Its purpose is to be an **information-access layer** that helps important video information cross language and cultural barriers [CONFIRMED]. Health, food, water and energy are *potential* application domains [CONFIRMED]. HyperLocalize does not solve the underlying physical problems in those domains [CONFIRMED].

## 2. The workflow

Create Localization Project → Upload and Analyze Source Video → Context-Aware Localization → Generate Localized Preview → Human Review → Regenerate Scene/Output if Required → Approve → Export Localization Package [CONFIRMED].

**Supporting concerns:** identity and consent control; users, providers and policies; quality inspection; audit and evidence [CONFIRMED].

**Actors:** Localization Manager, Reviewer / Linguist, Media Operator, Speaker / Identity Owner, Administrator, Auditor / Faculty Evaluator [CONFIRMED].

**Use cases:** UC1–UC9 [CONFIRMED]. "Record Consent" is included as a sub-use case [CONFIRMED, ADR 0013].

## 3. Context awareness

Localization decisions take into account the **source context and the target-audience context**. The system is not a simple translate-then-dub pipeline [CONFIRMED].

The concept covers language, meaning, visual and scene context, the target audience, and identity-related requirements [CONFIRMED].

The exact context inputs and method are [PROPOSED] (Phase 0 §4; ADR 0016 is pending the spike). Whether context measurably improves the output has not been measured yet [CONFIRMED that it is unmeasured].

## 4. Identity and consent

**Identity preservation is a core concern.** The system must respect each speaker's identity and consent boundary [CONFIRMED].

**Consent is a core safety and control requirement:**
- it is enforced in the backend before any use of identity [CONFIRMED];
- revocation must block new generation and cancel or halt pending jobs that use that identity [CONFIRMED, CLAUDE.md §5]. Stopping jobs that are already running is designed in ADR 0006 [CONFIRMED design];
- the effect of revocation on existing previews and exports must be defined [CONFIRMED].

**Voice cloning is one possible identity-preservation mechanism.** It is not the definition of the product [CONFIRMED].

**What identity covers at product level** (voice, face, other attributes) is [UNKNOWN].

**Status of the consent design:**
- The consent check and revocation cascade are designed in ADR 0006 [CONFIRMED design].
- The demo reset and withdrawal design (ADR 0020) is [PROPOSED].
- **Nothing is implemented** [CONFIRMED].

## 5. Human review, regeneration and approval

- All AI output is a **draft** [CONFIRMED].
- A human must review it before anything is released or exported [CONFIRMED].
- A reviewer can regenerate a problematic scene or output [CONFIRMED].
- Approval is a controlled gate before export [CONFIRMED].
- The system is **not autonomous** [CONFIRMED].

## 6. Audit, evidence, quality, providers and policies

**Audit.** The process is traceable. Every consent grant, revocation, approval, regeneration and export produces an audit record: who, what, when, which project or scene, and which consent version [CONFIRMED]. The record design is in ADR 0007 [CONFIRMED design, not built]. The full evidence-package format is [PROPOSED].

**Quality.** Rule-based checks on critical content (numbers, units, terminology), plus AI flags for possible meaning reversals that a reviewer must acknowledge, are an accepted design (ADR 0008) [CONFIRMED design, not built].

**Providers and policies.** AI stages sit behind provider interfaces, so they can be swapped or mocked [CONFIRMED, ADR 0005]. They are administered under UC8 [CONFIRMED].

## 7. The MVP (first demonstrable build)

**Project constraint** (not an MVP feature): zero budget [CONFIRMED, Q4].

| Item | Status |
|---|---|
| One language pair; one target locale per project; the MVP pair is **English → Tamil** | [CONFIRMED for the MVP: Q3, Q14] |
| Uploads of up to **5 minutes / 500 MB** | [CONFIRMED for the MVP, Q16] |
| No lip-sync and no face processing | [CONFIRMED for the MVP, Q5] |
| Demo deployment on one laptop | [CONFIRMED for the MVP, Q18] |
| MVP identity: a consented reference voice plus versioned consent, with stock-voice or subtitles-only fallback | [PROPOSED; ADR 0015 is provisional] |
| Implementation choices: modular monolith, Django (no DRF), PostgreSQL, a Postgres job queue, server-rendered pages with htmx, Docker Compose | [CONFIRMED implementation choices, ADRs 0001–0014]. These are **architecture, not the product** |
| Build slices S1–S4 | [PROPOSED] |
| Application code | **None exists** [CONFIRMED] |

## 8. The Phase 0 spike

The spike is a one-off experiment that evaluates **candidate** components against rules fixed before any results exist (`docs/SPIKE_PLAN.md`) [CONFIRMED]. It covers:
- transcription;
- context-aware translation;
- stock and cloned speech;
- speaker similarity;
- timing fit;
- speed;
- meaning checks;
- withdrawal.

The candidate models and providers are [PROPOSED; ADRs 0015–0019 are pending the spike]:
- faster-whisper;
- Gemini;
- Groq;
- IndicTrans2;
- IndicF5;
- Indic stock voices;
- Kaggle GPU.

Its thresholds, participants (Speakers A and B, raters R1 and R2) and its consent form are **spike decisions only** [CONFIRMED as spike-scoped]. The spike has **not been run**, and nothing has been measured [CONFIRMED].

## 9. The current demo scenario

- **The test case:** an English health-information script about ORS, localized into Tamil. It is used to test the workflow and the candidate components [CONFIRMED as a scenario].
- **Demo video length:** 1–3 minutes, which is a **TARGET** [PROPOSED, Phase 0 §5.2].
- **Demo mechanisms:** the demo reset, the golden project and the screen-recording rules [PROPOSED, ADR 0020].
- **Live consent revocation** is **designed, not implemented** [CONFIRMED].

## 10. Future work, and what HyperLocalize is NOT

**Proposed future enhancements:**
- visual context (keyframes, OCR) [PROPOSED];
- more language pairs [PROPOSED];
- several target languages per project [PROPOSED];
- background-music separation [PROPOSED];
- lip-sync and face processing, which are **future scope only** and would need their own consent design [CONFIRMED as future scope, Q5].

**HyperLocalize is NOT:**
- a health, ORS or Tamil-only application [CONFIRMED, user 2026-10-06];
- a voice-cloning product [CONFIRMED, user 2026-10-06];
- a competitor on raw dubbing quality [CONFIRMED, user 2026-10-06];
- a fully autonomous pipeline [CONFIRMED, CLAUDE.md §4; user 2026-10-06];
- a solution to physical problems in any domain [CONFIRMED, `docs/context/01`];
- something to describe as "production-ready", "secure", "GDPR compliant" or "100% accurate" [CONFIRMED, CLAUDE.md §2].

## 11. Still undecided

| Question | Status |
|---|---|
| Official requirements, problem statement and UML (Q1) | [UNKNOWN] |
| What identity covers at product level | [UNKNOWN] |
| How visual and scene context is used, and whether it belongs in the MVP | [UNKNOWN] |
| The final AI models and providers | [UNKNOWN; pending the spike] |
| The context-aware method, and whether context helps | [PROPOSED; not measured] |
| Languages the product supports beyond the MVP pair | [UNKNOWN] |
| Product-level limits on video length, size and format | [UNKNOWN] |
| The final export package and evidence-manifest format | [PROPOSED] |
| Whether the combination is genuinely novel | [UNKNOWN; no product or literature check done] |
| Quality, speed and accuracy figures | none measured |
| Deployment beyond the laptop demo | [UNKNOWN] |
| The effect of the team size on scope. The user reported on 2026-10-06 that they are working alone; this is not yet recorded (it contradicts Q2; SF8 is pending) | [UNKNOWN] |
