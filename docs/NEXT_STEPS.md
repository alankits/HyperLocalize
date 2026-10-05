# Next Steps

**Updated:** 2026-10-05 · **Phase:** 0 (Discovery and Design) · **Branch:** `phase0/spike-scripts`. **Do not merge to `master` yet** (user instruction, 2026-10-05).

## Done
- Phase 0 report (rev 4), ADRs 0001–0019, spike plan, third-party terms, ADR self-review and independent review.
- **Approved 2026-10-05:** ADRs 0001–0014 (Accepted), spike plan and §5 thresholds, Q10–Q18 defaults (Q16 stays 5 min / 500 MB, reconfirmed), "Record Consent" use case.
- Spike consent form and ORS test script drafted, with the independent review applied (`docs/spike/`). Both are still drafts.
- Spike tooling in `spike/` (standard library only), now including the **M2 tally** (`hlspike.translation_eval`, added 2026-10-05). 75 unit tests pass and 1 optional test is skipped; synthetic inputs only, not run on real data.
- **Second independent review of the consent form (2026-10-05): needs changes.** 2 blockers (Part D contradicts §5; withdrawal misses the demo-reset snapshot and other copies), 6 major, 8 minor. Details: `docs/spike/CONSENT_FORM_REVIEW.md`. **Not applied: waiting for approval.**
- Prerequisites: P4 done; P5 partly done; P8 partly done; P3 pending; P9 (Docker) added. Details in `SPIKE_PLAN.md` §1 and `STATUS.md`.

## Applied 2026-10-05 (user said "do A")
Preparation-review fixes to `CONSENT_FORM.md`, `TEST_SCRIPT.md`, `SPIKE_PLAN.md` §1–§3 and `spike/README.md`:
- Media folder `~/hl-spike-media/` and spike log `~/hl-spike-media/spike-log.md` (append-only, timestamped, no raw content; format in `SPIKE_PLAN.md` §2). `spike/work/` is now for synthetic data only.
- Docker memory limit 8 GB recorded in P8/P9.
- Signature block: 18+ confirmation, fields for the 4 named listeners and for listeners who know the speaker.
- Stale labels fixed: consent §4 heading names Gemini and Groq; script header says Q17 confirmed; consent 3.3 and slot A2 now say ZDR is on and the open check is speech-to-text coverage.
- Both documents are still **drafts**, not approved.

## Waiting on user / team decisions and actions (in order)
1. **Decisions still open:** who Speakers A and B are (matched gender and age) and who the named listeners are. The reply on 2026-10-05 gave placeholders only. These names go on the **signed paper forms**, not in git; the repo uses only the pseudonyms. Also create `~/hl-spike-media/` (`mkdir -m 700`) and confirm no cloud-sync client covers it.
2. **In parallel:**
   - **Faculty:** does an ethics process apply? Will they countersign? Fill in the consent blanks: withdrawal contact, N days, expiry, Part D end date, faculty guide.
   - **Facts:** two members check TEST_SCRIPT §4 independently against WHO 2005 Plan A, WHO/UNICEF 2004 and MoHFW, recording page numbers. Confirm the Indian ORS sachet size.
   - **Setup:** install Docker Engine and Compose (P9); wait for the HF approvals (P3); record Groq ZDR evidence for speech-to-text (P5); record the Ubuntu release (P8).
3. **Timed read-through** by Speaker A (stopwatch only, no recording). Then approve and freeze script v1.
4. **Approve the consent-review fixes** (`CONSENT_FORM_REVIEW.md`), then **approve consent form v1** (suggest a final critical-reviewer pass on the filled-in form). Then sign: faculty countersigns, and the speaker keeps a copy.
5. **R1:** the Tamil reference sentence (after checking IndicF5's reference-length guidance), the 27-segment reference translation, and the digit and word versions of the 10 clone-input segments. R2 checks all of it.
6. **Record** the test clip, reference clips and held-out clips.
7. **Team:** the verbatim reference transcript and hand-marked boundaries.
8. **R1 and R2:** fill in the Tamil forms in `spike/data/units.json` and `glossary.json`, and review `ta_number_word_stems.txt` (can run alongside steps 5–7). Then `python3 -m hlspike.freeze --write`. Only after that does R2 write the seeded errors.
9. **Spike runs:** need P3, P9 and the keys in `.env`.

## Exact next action
**User:** decide which consent-review fixes to apply (`CONSENT_FORM_REVIEW.md` #1–16; the assistant recommends all of them). Then the assistant edits `CONSENT_FORM.md` and fixes the clip-length mismatch in SPIKE_PLAN §2 (#14). Steps 1–2 above are still waiting on the team. No merges (user, 2026-10-05) and no freezes until approved.
