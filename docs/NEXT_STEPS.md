# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/discovery-report`

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan (rev 4), third-party terms, ADR self-review.
- Independent critical review of all ADRs and the spike plan; every finding resolved (`docs/ADR_REVIEW.md`, final section).
- Drafted spike consent form (`docs/spike/CONSENT_FORM.md`) and ORS test script (`docs/spike/TEST_SCRIPT.md`), both v1 drafts.
- Operating mode added to CLAUDE.md §11; reviewer agent at `.claude/agents/critical-reviewer.md` (usable as `critical-reviewer` from the next session).

## Waiting for user approval
1. ADRs 0001–0014 (status Proposed). Changes to consent (0006), audit (0007) and the data model (0014) in this round especially need sign-off.
2. Spike plan (`docs/SPIKE_PLAN.md`) and its [PROPOSED] thresholds in §5.
3. Proposed defaults for Q10–Q18 and the included use case "Record Consent" (ADR 0013).
4. Demo laptop specs (spike P8).
5. Consent form v1 and test script v1 (`docs/spike/`). Fill in the form's placeholders: withdrawal contact, response time, expiry date.

## Waiting on user actions (accounts and people)
- P3 Hugging Face gated access (IndicF5, IndicTrans2 dist-200M, Indic Parler-TTS); P4 Kaggle phone verification; P5 Gemini key (no billing) + Groq with ZDR.
- Verify the TEST_SCRIPT §4 health facts against the WHO source.
- R1 writes the Tamil reference-clip text; speakers A and B sign the consent form, then record.

## Exact next action
After approval:
1. Set each approved ADR's status to "Accepted" and merge `phase0/discovery-report` into `master`.
2. Complete spike prerequisites P3–P6, P8.
3. Run the spike per `docs/SPIKE_PLAN.md`.
4. Create `docs/EVALUATION.md` with measured results.
5. Update ADRs 0015–0019.
6. Phase 0 sign-off.
7. Start slice S1.
