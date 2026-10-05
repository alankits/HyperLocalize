# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/spike-scripts`. **Do not merge to `master` yet** (user instruction, 2026-10-05). **Do not run the spike on real data and do not record yet** (user instruction, 2026-10-05).

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults (Q16 stays 5 min / 500 MB, reconfirmed), "Record Consent" use case.
- Spike consent form and ORS test script drafted, with the first independent review and the preparation-review fixes applied. Both are still drafts.
- Spike tooling in `spike/` (standard library only), including the **M2 tally** (`hlspike.translation_eval`). 75 unit tests pass and 1 optional test is skipped; synthetic inputs only, not run on real data.
- **M2 choices approved 2026-10-05** and recorded in `SPIKE_PLAN.md` M2 and §5: linear-weighted κ for severity; a tie means within 5 points of the best; T2 vs T1 compares the same provider.
- **Second consent review (2026-10-05): all fixes #1–16 approved and applied** (`docs/spike/CONSENT_FORM_REVIEW.md`). The clip-length mismatch in SPIKE_PLAN §2 is fixed (8–11 s). Team-specific values are left blank, not invented.
- Prerequisites: P4 done; P5 partly done; P8 partly done; P3 pending; P9 (Docker) added. Details in `SPIKE_PLAN.md` §1 and `STATUS.md`.

## Order change caused by the consent fixes
The form may now be signed only **after** the test script is frozen and every Appendix A text exists, including R1's Tamil reference sentence and the TEST_SCRIPT §6 clone texts. Signing also needs **at least 24 h** after the explanation and the faculty guide's **required** countersignature. So R1's texts (step 4) now come **before** signing (step 5).

## Waiting on user / team decisions and actions (in order)
1. **Decisions still open:** who Speakers A and B are (matched gender and age), who the named listeners are (including the listeners who know the *other* speaker), and who R1 and R2 are. These names go on the **signed paper forms**, not in git; the repo uses only the pseudonyms. Also:
   - create `~/hl-spike-media/` (`mkdir -m 700`);
   - confirm no cloud-sync client covers it;
   - **exclude it from all backups**;
   - record whether the laptop disk is encrypted.
2. **In parallel:**
   - **Faculty:** ask whether institutional ethics approval is needed (record the answer and the date asked), and confirm they will countersign (now **required**). Choose who explains the form: the faculty guide or a non-speaker.
   - **Consent blanks:** withdrawal contact, N days, expiry, spike end date, Part D fixed end date and demo topic.
   - **Facts:** two members check TEST_SCRIPT §4 independently against WHO 2005 Plan A, WHO/UNICEF 2004 and MoHFW, recording page numbers. Confirm the Indian ORS sachet size. Check the IndicF5 model card for (a) the reference-length guidance and (b) the "no model is trained on your voice" statement, which is [INFERRED] in consent §1.
   - **Setup:** install Docker Engine and Compose (P9); wait for the HF approvals (P3); record dated Groq ZDR evidence for speech-to-text (P5; shown to Speaker A before signing 3.3); record the Ubuntu release (P8).
3. **Timed read-through** by Speaker A (stopwatch only, no recording). Then approve and freeze script v1.
4. **R1:** the Tamil reference sentence, the 27-segment reference translation, and the digit and word versions of the 10 clone-input segments. R2 checks all of it.
5. **Approve consent form v1** (suggest a final critical-reviewer pass on the filled-in form). Explain it, wait at least 24 h, then sign with Appendix A initialled. The faculty guide countersigns, and the speaker keeps a copy.
6. **Record** the test clip, reference clips and held-out clips.
7. **Team:** the verbatim reference transcript and hand-marked boundaries.
8. **R1 and R2:** fill in the Tamil forms in `spike/data/units.json` and `glossary.json`, and review `ta_number_word_stems.txt` (can run alongside steps 4–7). Then `python3 -m hlspike.freeze --write`. Only after that does R2 write the seeded errors.
9. **Spike runs:** need P3, P9 and the keys in `.env`.

## Exact next action
Waiting on the user and team for steps 1–2. The assistant can, when asked: (a) run a critical-reviewer pass on the revised consent form; (b) propose the ADR 0006/0012 change for the `demo_reset` snapshot gap (`STATUS.md` known issues; needs approval). No merges, no spike runs on real data, no recordings and no freezes until approved.
