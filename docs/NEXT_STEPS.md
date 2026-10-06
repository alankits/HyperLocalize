# Next Steps

**Updated:** 2026-10-06 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/spike-scripts`. **Do not merge to `master` yet** (user instruction, 2026-10-05). **Do not run the spike on real data and do not record yet** (user instruction, 2026-10-05).

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults (Q16 stays 5 min / 500 MB, reconfirmed), "Record Consent" use case.
- Spike consent form and ORS test script drafted, with the first independent review and the preparation-review fixes applied. Both are still drafts.
- Spike tooling in `spike/` (standard library only), including the **M2 tally** (`hlspike.translation_eval`). 75 unit tests pass and 1 optional test is skipped; synthetic inputs only, not run on real data.
- **M2 choices approved 2026-10-05** and recorded in `SPIKE_PLAN.md` M2 and §5: linear-weighted κ for severity; a tie means within 5 points of the best; T2 vs T1 compares the same provider.
- **Second consent review (2026-10-05): all fixes #1–16 approved and applied** (`docs/spike/CONSENT_FORM_REVIEW.md`). The clip-length mismatch in SPIKE_PLAN §2 is fixed (8–11 s). Team-specific values are left blank, not invented.
- **2026-10-06:**
  - **Round-2 consent review** (1 blocker, 4 major, 4 minor; `CONSENT_FORM_REVIEW.md` round 2): **P1–P8 approved and applied** to `CONSENT_FORM.md`, with P6 also reordering `TEST_SCRIPT.md` §7.
  - **P9 approved and applied** to `SPIKE_PLAN.md`: P6 permissions aligned; in M4, A's listeners rate both clones. Rule 4 when ECAPA is skipped uses **Option A**: A's clone "same person?" median ≥ 3 **and** B's clone ≤ 2. If B hasn't given 3.4 and 3.6, the condition is not met.
  - **Interim rule** (approved, then superseded the same day by ADR 0020): no real voice in any demo-reset snapshot or golden project.
  - **ADR 0020 proposed** (`docs/adr/0020-demo-reset-and-identity-withdrawal.md`): the demo reset rebuilds instead of restoring, an `OfflineCopy` register, and owner-level withdrawal. It amends ADRs 0006, 0012 and 0014. Round-1 review: needs changes (2 blockers); revision 2 applied all 14 fixes. Round-2 review: approve with changes; **revision 3** applied N1–N7, the simplification and the N4 consent wording (approved by the user). Round-3 review: approve with changes; **revision 4** applied M1–M6 (M4 option a: the golden project is built once by hand, stock voices, real approval). Spot-check: ready. **Accepted by the user 2026-10-06; amendments applied to ADRs 0006, 0007, 0011, 0012 and 0014; interim rule superseded.**
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
   - **Setup:** install Docker Engine and Compose (P9); wait for the HF approvals (P3); record dated Groq ZDR evidence for speech-to-text (P5; shown to Speaker A before signing 3.3).
3. **Timed read-through** by Speaker A (stopwatch only, no recording). Then approve and freeze script v1.
4. **R1:** the Tamil reference sentence, the 27-segment reference translation, and the digit and word versions of the 10 clone-input segments. R2 checks all of it.
5. **Approve consent form v1** (suggest a final critical-reviewer pass on the filled-in form). Explain it, wait at least 24 h, then sign with Appendix A initialled. The faculty guide countersigns, and the speaker keeps a copy.
6. **Record** the test clip, reference clips and held-out clips.
7. **Team:** the verbatim reference transcript and hand-marked boundaries.
8. **R1 and R2:** fill in the Tamil forms in `spike/data/units.json` and `glossary.json`, and review `ta_number_word_stems.txt` (can run alongside steps 4–7). Then `python3 -m hlspike.freeze --write`. Only after that does R2 write the seeded errors.
9. **Spike runs:** need P3, P9 and the keys in `.env`.

## Exact next action
**All open design decisions in this thread are closed.** The next steps are with the team (steps 1–2 above):
- names on the paper forms;
- the media folder, cloud-sync and backup checks, and disk encryption;
- the faculty ethics question and countersignature;
- the consent blanks;
- the TEST_SCRIPT §4 fact check;
- Docker (P9), the HF approvals (P3), and the Groq evidence (P5); P8 is done (Ubuntu 26.04.1 LTS).

Then the timed read-through and the script freeze (step 3).

**Consistency pass done (2026-10-06):** consistent, with minor fixes. All the wording fixes are applied, including the spike live script (no live approval invalidation in a rehearsal project) and the ADR 0003 lock order.

**One open user decision:** after the spike, `external_transcription` (Groq speech-to-text) can't pass the gate, because Part D has no tick for it. Choose:
- (a) local ASR only after the spike (no form change; recommended);
- (b) add a Part D tick D5 for external transcription (a consent form change).

**GitHub:** no remote is configured. Nothing has been pushed; all commits are local only.

The consent form is still a draft and needs your approval (step 5) after the blanks and Appendix A texts exist. No Part D signature before that. No merges, no spike runs on real data, no recordings and no freezes until approved.
