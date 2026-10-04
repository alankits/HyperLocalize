# ADR Review: ADRs 0001–0008

| | |
|---|---|
| **Date** | 2026-10-05 |
| **Reviewer stance** | A strict external reviewer, not the author |
| **Inputs** | Q1–Q8 answers (2026-10-05): no official UML or rubric; ≤4 students, intermediate Python, basic JS/React, little DevOps, about 5 months; **English → Tamil**; free tiers + ₹2,000/month, no GPU, hosted APIs only; no lip-sync; external APIs allowed (team's own voices only); 2 bilingual raters; academic project with a live demo and viva |
| **Criteria** | (1) consistent with the answers; (2) consent re-checked at every stage boundary, with mid-job cancellation; (3) honest audit threat model, chain head in exports, no claim of tamper resistance; (4) Tamil-aware verification split; (5) no overclaimed novelty; (6) over- or under-engineered for the team and the live demo; (7) defensible in a 2-minute viva |

All changes listed below **have been applied** to the ADR files. Every ADR remains **Proposed** until you approve it.

## Review table

| ADR | Verdict | Changes made | Remaining risks |
|---|---|---|---|
| **0001** Modular monolith | **Approve with changes** | Named Django (ADR 0009). Reduced 12 abstract modules to **9 Django apps** mapped to use cases. Banned signals for consent and audit. Dropped "import-boundary tooling" (over-engineered for 4 people). Added a 2-minute viva line. | Boundaries depend on discipline only; one DB is the scale limit (stated). |
| **0002** PostgreSQL | **Approve** (no change to the decision) | Limited Postgres operations to one Compose service with a one-command start (little DevOps experience). Viva line added. | The team must understand locking well enough to explain ADR 0006; encryption at rest and backups are not claimed. |
| **0003** Job queue | **Approve with changes** | **Decided: a hand-written `Job` model + `run_worker` command, no library.** A library would still need our cancellation and checkpoints, so it adds concepts without removing work. One worker for the MVP. Stale-job recovery via heartbeat. Rate-limit handling moved to the adapters. Retry only on transient errors; `CONSENT_REVOKED` is terminal. Idempotent versioned writes. UI progress polling. | The team owns retry and crash-recovery correctness; this needs explicit tests (concurrent claim, crash, retry limit, cancel in each state). |
| **0004** Media storage | **Approve with changes** (minor) | Added MVP upload limits (≤ 5 min, ≤ 500 MB, ffprobe check) as **proposed defaults**. Named volume in Compose. Viva line. | Filesystem deletion is not secure erasure (stated); limits are a proposed default (Q16 unanswered). |
| **0005** Provider abstraction | **Approve with changes** | **Added a `ProviderUsage` ledger and a hard monthly budget cap** (default ₹1,800 below the ₹2,000 limit). Without it, a retry bug could spend the whole budget; that was under-engineered. Added the rule that **identity data goes only to providers with training disabled for our account** (verified: the Gemini free tier uses content to improve products). Added per-provider rate-limit handling, timeouts and a 5-type error model. Defined interface methods. Mocks are never used silently in a live demo. | Ledger costs are estimates from published prices and can drift; check against dashboards monthly. |
| **0006** Consent gate | **Approve with changes** | Criterion 2 met: checkpoints **before synthesis (per segment), before render/mix, before export build and save**, plus request, claim, enrolment, approval and serving; mid-job cancellation behaviour is defined step by step. **Bug found:** the revoke-vs-save race fix used `SELECT … FOR SHARE`, which **Django's ORM does not provide** (verified in the Django 6.1 docs). Changed to `select_for_update()` on both sides: simpler to explain, still correct, and no cost with one worker. Added a visible **"deletion pending"** state for provider-side deletion, consent evidence (signed form, named processors), and demo timing based on spike M6. | Time-to-stop is bounded by the longest provider call (to be measured). Provider deletion can only be shown at the API level. Retention of quarantined media is a proposed default. |
| **0007** Audit records | **Approve with changes** | Criterion 3 met: the threat model says **tamper-evident, not tamper-resistant**; the chain head goes into every export manifest; the banned word is absent. **Gap found:** no canonical serialisation, so verification could fail on formatting alone; **canonical JSON rules added**. The separate restricted DB role is moved to **optional hardening** (operations burden), and the threat model now states honestly that the table owner can disable the trigger. Added a `verify_audit_chain` command and its result shown on the Auditor screen. | Anyone with DB access can rebuild the chain; only exported chain heads detect that. Forged appends are not detectable without a keyed hash (future ADR). |
| **0008** Verification | **Approve with changes** | Criterion 4: **Tamil number handling added**: Western digits with Indian and Western digit grouping, Tamil digits ௦–௯, the non-positional numerals ௰ ௱ ௲, and a bounded Tamil number-word lexicon including combined (sandhi) forms, lakh and crore. **Fail-safe `UNVERIFIABLE` result** so unparsed numbers are never passed silently. Glossary entries carry **accepted inflected forms** (from the raters). The unit lexicon is built by the raters, not from memory. Negation is explicitly AI-flagged, because Tamil negation is built into the verb. Separate **speech script** (numbers as words) if spike M4 shows the TTS misreads digits. | The number-word lexicon and accepted forms will be incomplete; coverage is measured in spike M3. False alarms cost reviewer time. |

## Cross-cutting findings

| # | Finding | Type | Where fixed |
|---|---|---|---|
| F1 | The `FOR SHARE` lock in the consent design isn't available in Django's ORM | Correctness bug in the design | ADR 0006 |
| F2 | No spending guard against a ₹2,000 limit | Under-engineered (a live risk) | ADR 0005 |
| F3 | Free-tier LLM terms allow training on submitted content | Privacy gap | ADR 0005, `SPIKE_PLAN.md` P6 |
| F4 | Hash chain without canonical serialisation | Under-engineered | ADR 0007 |
| F5 | Restricted DB role exceeds team DevOps capacity | Over-engineered for the MVP | ADR 0007 (made optional) |
| F6 | Job library choice was left open | Indecision | ADR 0003 (hand-written) |
| F7 | No plan for API or network failure during the live demo | Under-engineered (demo risk) | ADR 0012 (new) |
| F8 | Phase 0 recommended React + TypeScript, but the team has basic JS/React | Inconsistent with Q2 | ADR 0010 (HTMX) |
| F9 | Granting consent has no use case | Gap in the use-case model | ADR 0013 (proposed «include» "Record Consent") |
| F10 | Number handling assumed Western digits only | Inconsistent with Q3 (Tamil) | ADR 0008 |

## Novelty check (criterion 5)

None of ADRs 0001–0008 claims novelty. The classifications in `docs/PHASE0_DISCOVERY.md` §9 stand:
- the consent cascade (ADR 0006) is **[ENHANCEMENT]**;
- rule checks and AI flags (ADR 0008) are **[ENHANCEMENT]**;
- the only **[PROPOSED NOVELTY]** is the *combination* of critical-information verification, a mandatory review gate and an evidence-carrying export, for high-stakes domains. That claim still needs a product and literature check, which has not been done.

## Viva check (criterion 7)

Every ADR now ends with a "Viva in 2 minutes" line. The reviewer's judgement is that ADR 0006 (locking) and ADR 0007 (what the hash chain does and does not detect) are the two that need **rehearsal**. Both have exact one-paragraph explanations in their ADRs.
