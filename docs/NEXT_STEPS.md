# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/spike-scripts` (spike tooling; merge to `master` when you're happy)

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults, "Record Consent" use case.
- Spike consent form and ORS test script drafted, independent review applied (`docs/spike/`).
- Spike tooling in `spike/` (stdlib only): M1 scorer, ADR 0008 checks, freeze, M3 seeded eval, M5, M6 harness, rule 6. 51 unit tests pass on synthetic inputs.

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

- R1/R2 fill in the Tamil forms in `spike/data/units.json` and `glossary.json`, and review `ta_number_word_stems.txt`. Then run `python3 -m hlspike.freeze --write` and commit `FROZEN_RULES.json`. Only after that does R2 write the seeded errors.
- Confirm whether this machine (i5-13450HX, 16 threads, about 15 GB RAM, as seen by `hlspike.bench`) is the demo laptop. Give the OS and Docker memory limit.

## Exact next action
The next tooling needs models and keys: the faster-whisper runner (M1, local, needs about 1–2 GB of model download), the M2 MQM/chrF tally, and the ECAPA script (M4). The assistant can write the M2 tally now (no external calls), and the runners once P3 and P5 are done.
Then: run the spike → `docs/EVALUATION.md` → update ADRs 0015–0019 → Phase 0 sign-off (with critical-reviewer) → slice S1.
