# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `master`

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults, "Record Consent" use case.
- Spike consent form and ORS test script drafted, independent review applied (`docs/spike/`).

## Waiting for user approval
1. Consent form v1 (`docs/spike/CONSENT_FORM.md`), after its placeholders are filled in: withdrawal contact, N days, expiry, Part D end date, faculty guide.
2. Test script v1 (`docs/spike/TEST_SCRIPT.md`), after the §4 health facts are checked and a timed read-through is done.

## Waiting on user actions
- **P8:** demo laptop specs (CPU and cores, RAM, OS, Docker memory limit).
- **P3:** Hugging Face gated access (IndicF5, IndicTrans2 En-Indic dist-200M, Indic Parler-TTS).
- **P4:** Kaggle account with phone verification.
- **P5:** Gemini key (project without billing); Groq account, and check whether Zero Data Retention can be enabled on the free plan (decides whether slot A2 runs).
- **P6:** speakers A and B (matched gender and age) sign the consent form.
- Two team members check TEST_SCRIPT §4 against WHO 2005 Plan A (with page numbers).
- R1 writes the Tamil reference text and the Tamil digit and word versions of the 10 clone-input segments; R1 then writes the reference translation.

## Exact next action
While the user works on the above, the assistant can write the throwaway spike code in `spike/` (local only, no external calls until P5 and P6 are done):
the M1 WER and critical-token scorer, the ADR 0008 rule checks (frozen before R2 writes the seeded errors), the M5 timing script, and the M6 timing harness.
Then: run the spike → `docs/EVALUATION.md` → update ADRs 0015–0019 → Phase 0 sign-off (with critical-reviewer) → slice S1.
