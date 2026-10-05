# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/spike-scripts`. **Do not merge to `master` yet** (user instruction, 2026-10-05).

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults (Q16 stays 5 min / 500 MB, reconfirmed), "Record Consent" use case.
- Spike consent form and ORS test script drafted, with the independent review applied (`docs/spike/`). Both are still drafts.
- Spike tooling in `spike/` (standard library only). 51 unit tests pass on synthetic inputs; not run on real data.
- Prerequisites: P4 done; P5 partly done; P8 partly done; P3 pending; P9 (Docker) added. Details in `SPIKE_PLAN.md` §1 and `STATUS.md`.

## On hold (user, 2026-10-05)
Fixes to `CONSENT_FORM.md` and `TEST_SCRIPT.md`, found in the preparation review. **Not applied:**
- The media location conflict: both documents say "outside the git repository", but `spike/README.md` says `spike/work/`, which is inside the repo (git-ignored).
- The "spike log" location and format are not defined anywhere.
- No age (18+) confirmation in the signature block.
- No field for the names of the "up to 4 named" listeners in consent 3.4.
- Stale labels: the consent §4 heading says "Google Gemini" only; the script header says "Q17 proposed default"; consent 3.3 is worded as conditional on ZDR.

## Waiting on user / team decisions and actions (in order)
1. **Decisions:** the media folder path (outside the repo and outside cloud sync), the spike-log location, Speakers A and B (matched gender and age), the named listeners, and the **Docker memory limit (P9)**.
2. **In parallel:**
   - **Faculty:** does an ethics process apply? Will they countersign? Fill in the consent blanks: withdrawal contact, N days, expiry, Part D end date, faculty guide.
   - **Facts:** two members check TEST_SCRIPT §4 independently against WHO 2005 Plan A, WHO/UNICEF 2004 and MoHFW, recording page numbers. Confirm the Indian ORS sachet size.
   - **Setup:** install Docker Engine and Compose (P9); wait for the HF approvals (P3); record Groq ZDR evidence for speech-to-text (P5); record the Ubuntu release (P8).
3. **Timed read-through** by Speaker A (stopwatch only, no recording). Then approve and freeze script v1.
4. **Approve consent form v1** (suggest a critical-reviewer pass on the filled-in form). Then sign: faculty countersigns, and the speaker keeps a copy.
5. **R1:** the Tamil reference sentence (after checking IndicF5's reference-length guidance), the 27-segment reference translation, and the digit and word versions of the 10 clone-input segments. R2 checks all of it.
6. **Record** the test clip, reference clips and held-out clips.
7. **Team:** the verbatim reference transcript and hand-marked boundaries.
8. **R1 and R2:** fill in the Tamil forms in `spike/data/units.json` and `glossary.json`, and review `ta_number_word_stems.txt` (can run alongside steps 5–7). Then `python3 -m hlspike.freeze --write`. Only after that does R2 write the seeded errors.
9. **Spike runs:** need P3, P9 and the keys in `.env`.

## Exact next action
Waiting on the user for the step 1 decisions. When asked, the assistant can apply the on-hold document fixes, or write the M2 MQM/chrF tally (no external calls). No code changes, merges or freezes until approved.
