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

---

## Addendum: Q4 changed to zero budget (2026-10-05)

New Q4: **zero spend**; free tiers and open-source models only; no local GPU; Kaggle Notebooks (free, about 30 GPU h/week) may run GPU-heavy steps. Requirements:
1. every AI provider has a free alternative and a named mock;
2. document the Gemini free-tier training terms and IndicF5's non-commercial status;
3. measure IndicF5 on CPU vs. Kaggle GPU, and have a demo plan for slow CPU synthesis.

| ADR | Verdict | Changes made | Remaining risks |
|---|---|---|---|
| 0003 Job queue | Approve with changes | Added the `DISPATCHED` state for Kaggle batch jobs (with a dispatch timeout instead of the heartbeat), an inference subprocess for local models (killable), and `purge_identity_data`. | Remote poll logic and subprocess management need tests. |
| 0005 Providers | Approve with changes (**rewritten**) | Replaced the ₹ cap with a **zero-spend policy** (providers needing a payment method are ineligible). Added a **provider chain per stage** (free primary → free alternative), with the adapter that ran shown to the reviewer. **Mocks are never in a live chain, and export is refused if any artefact came from a mock.** Free-quota ledger with 80% warnings. Free-tier data-use rule (Gemini: script text only). | No second independent free Tamil cloning model exists; resilience there comes from two runtimes plus the stock-voice fallback (stated honestly). |
| 0006 Consent | Approve with changes (**rewritten**) | Runtime-specific stop behaviour. **Local:** the inference subprocess is killed (stops in seconds). **Kaggle:** no cancel command exists (verified in the Kaggle CLI docs), so the guarantee is "output never imported; remote kernel and dataset deleted", not "remote compute stops". The voice profile is now our own reference clip (no third-party clone object). Kaggle is named as a processor. | Whether `kernels delete` stops a running kernel is [UNVERIFIED] (spike M9). Kaggle's retention after deletion is outside our control. |
| 0008 Verification | Minor change | Removed the budget-cap reference; the meaning-check has a fail-safe `CHECK_UNAVAILABLE` flag. | — |
| 0009, 0011, 0013, 0014 | Minor change | "Budget cap" policy replaced by provider chain order and quota warnings. | — |
| 0012 Deployment | Approve with changes | The worker hosts the local inference subprocess; model weights are kept in a volume; the laptop's RAM and CPU are now a constraint; **demo plans A/B/C** added; quota check before the demo. | Laptop specs are unknown (spike P8). |
| 0015–0018 | Rewritten, still pending | Paid providers removed. IndicF5 for cloning; MMS-TTS / Indic Parler-TTS / ElevenLabs free for stock voice; Gemini free / Groq / IndicTrans2 for translation; Groq / faster-whisper for ASR. Each has a free alternative and a mock. | Tamil quality of every option is unmeasured. |
| **0019** Kaggle batch runtime | New, pending | Automated private dataset + private GPU kernel through the official CLI; consent checked at dispatch and at import; remote copies deleted. | Depends on one phone-verified account and on Kaggle's free quota. |

**A discrepancy you should know about:** you asked me to document IndicF5 as non-commercial. Its **Hugging Face model card states MIT**. However, the GitHub repo shows no licence file, and IndicF5 builds on F5-TTS, whose official weights are **CC-BY-NC-4.0**. The docs therefore record the MIT label **and** our conservative non-commercial treatment, rather than claiming the model is officially non-commercial.

---

## Independent review (2026-10-05)

**Reviewer:** the `critical-reviewer` brief (`.claude/agents/critical-reviewer.md`), run as two read-only agents with fresh context. The custom agent type only loads in a new session, so the built-in read-only `Plan` agent ran the same brief.

**Verdicts before fixes:**
- Approve: 0002, 0010, 0011, THIRD_PARTY_TERMS.
- Approve with changes: all others.
- Reject: none.

| # | Severity | Finding | Resolution |
|---|---|---|---|
| R1-1 | **Critical** | 0006 locked "the Consent row", but revocation *inserts* a new row, so the race wasn't closed | **Fixed:** lock the stable `IdentityOwner` row; a save succeeds only if the job's consent version is still the latest ACTIVE one; new test (0006 §4, 0014) |
| R2-1 | **Critical** | 0014 VoiceProfile still had provider-clone fields | **Fixed:** local clip fields (0014) |
| R1-2 | Major | Groq ASR sent source audio out with no consent check; "voice data stays on the laptop" was false | **Fixed:** faster-whisper is now the default; Groq needs `external_transcription` consent + `allow_external_audio` (new CP0) (0005, 0006, 0017) |
| R1-3 | Major | The Django admin could un-quarantine artefacts | **Fixed:** read-only fields, audited policy changes, a test (0009) |
| R1-4 | Major | One worker: long CPU synthesis blocks the demo | **Fixed:** two lanes, `synthesis` and `default` (0003, 0001, 0012) |
| R1-5 | Major | Heartbeat only at checkpoints, so a live slow job could be reaped | **Fixed:** heartbeat from the 1-second loop (0003) |
| R1-6 / R2-3 | Major | Cancellation: state or flag? The reviewers **disagreed** (R1: flag; R2: state); the diagram was also missing transitions | **Chose the flag** (simpler, one source of truth); added DISPATCHED transitions, `cancel_reason`, `dispatched_at`, `remote_ref`, nullable targets (0003, 0014). **R2's suggestion of a `CANCEL_REQUESTED` state was not adopted.** |
| R1-7 | Major | No lock order, so deadlocks were possible | **Fixed:** IdentityOwner → Job → artefacts → AuditChainHead last (0003, 0007) |
| R1-8 | Major | Tamil number-word parser too large for the team | **Fixed:** the model is instructed to write digits; parse Western and Tamil digits; words are `UNVERIFIABLE`; the lexicon is stretch scope (0008) |
| R2-2 | Major | Kaggle copies were not tracked | **Fixed:** `RemoteCopy` entity, recorded before upload (0014, 0019) |
| R2-4 | Major | No per-segment audio entity | **Fixed:** `SynthesisedSegment` (0014, 0006) |
| R1-9 / R2-5 | Major | "Gemini only for scripted text" was not enforced | **Fixed:** `Project.data_classification`; the chain skips Gemini otherwise; audited; tested (0005, 0014, 0016) |
| R2-6 | Major | Seeded errors written by the check authors | **Fixed:** rules frozen first; R2 writes the errors (spike M3) |
| R2-7 | Major | 7 outputs per segment; rater hours underestimated | **Fixed:** one Groq model chosen by pre-screen (5 outputs); 5–6 h per rater (spike) |
| R2-8 | Major | Tie margins meaningless with n = 1; trivial similarity bar | **Fixed:** count-based ties; pooled median; different-speaker clone control (spike §5, M4) |
| R2-9 | Major | Bare-metal timings ≠ Docker; RAM exhaustion | **Fixed:** M6 runs inside Compose on the demo laptop; one model loaded at a time (0005, spike) |
| R2-10 | Major | Plans C/D missing from 0012 | **Fixed:** 0012 references spike §6 as authoritative and lists all plans |
| R2-11 | Major | Kaggle adopted when it *works*, not when it's *needed* | **Fixed:** adopted only if CPU fails live use **and** overnight CPU exceeds 8 h (0019, rule 6) |
| R1-10…14, R2-12…18 | Minor | Gate `job` parameter; stale hosting text; M3→M4 reference; TRUNCATE trigger; purge timing and expiry sweep; offline fallback; mock "(tests only)"; processor list; preview models; UML actors; batch per project; Scene states | **All fixed** |
| Honesty | — | Unlabelled "output deleted with the kernel"; past-tense "we measured"; "fine for 1–5 min"; unlabelled "stronger baseline"; "we kill the job" for Kaggle; "because our AI is hosted" | **All fixed** (now [UNVERIFIED] / [INFERRED] / future tense / corrected) |
| Demo risks | — | Re-review step missing from the script; rehearsals destroy the demo state; live Kaggle dispatch adds risk; audit view noise | **Fixed:** scripted re-review, `demo_reset` fixture, Kaggle dispatch optional, audit filter (0012, 0007, spike §6) |

**Where I disagree with the reviewers:** only on the state-vs-flag conflict above, which is resolved in favour of reviewer 1. Every other finding was accepted.

**Still open after fixes (reviewer-flagged, can't be resolved by editing):**
- Some external facts can't be verified by the reviewer (Groq free-plan limits and ZDR availability, the Kaggle quota, Gemini and ElevenLabs terms quotes). They are labelled; re-check before the final evaluation.
- Every threshold marked [PROPOSED] needs your confirmation.


---

## Independent review: spike consent form and test script (2026-10-05)

**Reviewer:** `critical-reviewer` agent, with a fresh context. **Verdict:** both documents "approve with changes". All 24 findings were applied:

| Findings | Change |
|---|---|
| Kaggle deletion and Groq ZDR overclaimed (#1, #2) | The form now states that Kaggle jobs can't be cancelled and that output deletion is [UNVERIFIED] (tested in M9). Groq audio is sent **only if** ZDR can be enabled; otherwise A2 is dropped (SPIKE_PLAN updated). |
| Missing consent for uses (#3, #4, #9, #11, #12, #13) | New permissions: 3.0 (recording and local processing) and 3.6 (clone used as a comparison sample). Listeners are limited and named (SPIKE_PLAN M4 updated). Intelligibility uses local faster-whisper. The simulated revocation (M9) and Kaggle-stored cloned output are disclosed. |
| Clone might speak machine output (#5) | Clone input is fixed to R1's reference translation of 10 listed segments (TEST_SCRIPT §6; SPIKE_PLAN M6 updated). |
| Voluntariness for teammates (#10) | Statement that saying no has no effect on role or marks; faculty guide as escalation contact and countersignatory. |
| Phone and cloud-sync leaks (#8) | Laptop recording preferred; airplane mode and backup off on phones; phone copy deleted and logged; no synced folders. |
| Part D and expiry (#14), pseudonym traceability (#15), non-system uses (#16) | Part D split into D1–D4 and stated to extend expiry only for the ticked uses. Pseudonym caveat added. Spike-only uses marked. ECAPA row added to THIRD_PARTY_TERMS ([UNVERIFIED] licence). |
| S17 dosing likely wrong (#6), S14 ambiguous (#7) | S17 → "teaspoonful every 1 to 2 minutes" [UNVERIFIED]; "rule of thumb" moved to a non-dosing line (S12); S14 gains "after each loose stool"; "high fever" → "fever". |
| Rating protocol (#17–#22) | B matched to A; held-out clip for ECAPA; S24–S26 rated as one unit; critical-token list and normalisation fixed in advance; whole-take re-record; 5 separate calibration sentences. |
| Length and reference clips (#20, #23, #24) | S28 dropped (27 segments, 251 words); timed read-through required before freezing; references shortened to 8–11 s (IndicF5 guidance [UNVERIFIED]); pack-size check added. |
| Label misuse | `[TO VERIFY]` → `[UNVERIFIED]`. |

**Not resolved, needs a human:** every health fact in TEST_SCRIPT §4 still has to be checked against the WHO source by two team members.
