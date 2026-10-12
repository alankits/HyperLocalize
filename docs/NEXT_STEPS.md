# Next Steps

**Updated:** 2026-10-12 · **Phase:** 1 (MVP build, authorized 2026-10-06) · **Branch:** `phase0/spike-scripts`. **Do not merge to `master` yet** (user instruction, 2026-10-05). **Do not run the spike on real data and do not record yet** (user instruction, 2026-10-05).

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
  - **Interim rule approved:** no real voice in any demo-reset snapshot or golden project until ADR 0020 is approved (ADR 0012 note, SPIKE_PLAN §6, consent Part D).
  - **ADR 0020 proposed** (`docs/adr/0020-demo-reset-and-identity-withdrawal.md`): the demo reset rebuilds instead of restoring, an `OfflineCopy` register, and owner-level withdrawal. It amends ADRs 0006, 0012 and 0014. Round-1 review: needs changes (2 blockers); revision 2 applied all 14 fixes. Round-2 review: approve with changes; **revision 3** applied N1–N7, the simplification and the N4 consent wording (approved by the user). Round-3 review: approve with changes; **revision 4** applied M1–M6 (M4 option a: the golden project is built once by hand, stock voices, real approval). **Spot-check: ready for user approval.** **Not approved yet.**
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

## Framing audit (2026-10-06)
- **Canonical product definition:** `docs/PRODUCT.md`. HyperLocalize is a general localization workflow. Health/ORS and English → Tamil are the spike and demo scenario only.
- **Applied (wording only):**
  - ADR 0013: language- and provider-neutral use cases;
  - ADR 0014: MVP values marked;
  - ADR 0008 and Phase 0 §0 and §9: the "high-stakes" claim reworded as an emphasis;
  - ADR 0015: MVP qualifier;
  - CLAUDE.md §1: pointer to PRODUCT.md.
- **ADR 0020:** reverted to Proposed; amendments rolled back. Revision 5 decouples the product consent model from the spike's Part D. The interim rule (no real voice in any snapshot or golden project) is **in force again**.
- **Not applied (optional SHOULD FIX items):**
  - SF2: ADR 0008 title "(Tamil-aware)";
  - SF3: ADR 0004 "MVP upload limits";
  - SF4: ADR 0006 Context;
  - SF5: ADR 0016 and 0018 titles;
  - SF7: Phase 0 header and §0 stack;
  - SF8: team size is now one developer.

## Session 2026-10-12
**Done and verified:**
- Re-ran the suites before any change: 126 pass and 1 is skipped; spike: 75 pass and 1 is skipped.
- **Free-quota warnings (ADR 0005, UC8).**
  - Code: `pipeline/quota.py`, the Policies page, and `check_providers`.
  - The Administrator enters the limits; none are built in, and an unconfigured adapter is never shown as "safe".
  - Warnings at 80% and 100% over rolling 24 h or 7 day windows. Warn only: nothing is blocked.
  - Limits are offered only where usage is really recorded: real localization and meaning-check adapters, in requests.
  - No schema change: a new `Policy` key, `provider_quota_limits`.
- **UML render check:** all 10 Mermaid diagrams render (mermaid-cli 11.4.2). One sequence diagram was broken by semicolons; fixed.
- **Browser walk-through:** eight role pages in headless Chromium, all HTTP 200; screenshots in `docs/screenshots/`.
  - Two UI bugs found and fixed: policy labels read "Separationofduties", and audit hashes ran past the panel edge.
- Stale STATUS entries corrected: UC8 users via Django admin and the retention sweeps were already built.
- **Tests: 139 pass, 1 optional skipped** (126 + 13 new).

**Not done / known gaps:**
- Transcription and speech usage is not metered.
- The Kaggle GPU-hours quota (ADR 0019) has no adapter yet.
- Two Gemini adapters that share one account are counted separately.

## Exact next action
**User actions and decisions (blocking the real-data spike and real providers):** unchanged from 2026-10-06.
1. GitHub: give the URL of an empty private repo; the assistant adds the remote and pushes. **Nothing is backed up off this laptop yet.**
2. Install Docker: `sudo apt install docker.io docker-compose-v2`. Then the assistant runs `docker compose up` and records the result.
3. Solo plan (`docs/SOLO_PLAN.md`): choose the Speaker B option (A: volunteer; B: dataset impostor set, which needs approval). Recruit a Tamil-literate rater (R1).
4. External transcription after the spike: (a) local ASR only, or (b) add a D5 tick.
5. **Gemini (2026-10-12):**
   - **Done:** key in `.env`; live smoke test (`docs/trials/2026-10-12-gemini-live-trial.md`).
   - **Approved and applied:**
     - the default model is now `gemini-3.5-flash`;
     - 429 classification and retry;
     - provider skip/fallback audit (ADR 0005 implementation note).
   - **Independent review: approve with changes.** In-scope fixes applied: demo-mode `NoProviderAvailable` skips are audited, the fallback records `after`, the retry has a 75 s budget, and comments are corrected.
   - **Waiting on the user** (decisions D1–D4 in the session summary):
     - **D1:** move the meaning check out of the consent lock and the web request (review #1, Major).
     - **D2:** batch the meaning check per scene (13 → about 4 requests per run).
     - **D3:** count every HTTP attempt in the quota ledger.
     - **D4:** quota policy values. The 20/day pool is shared by both adapters; the ledger counts adapters separately.
   - **Re-verify live after the daily reset** (about 12 h 47 min after 2026-10-12 ~15:30).
   - Rotate the key before any real data is used.

**Next engineering tasks (no approval needed):**
- importing pre-rendered cloned audio into the demo seed (stock or MOCK only until real consent exists; interim rule);
- a browser walk-through that submits forms (review → approve → export refusal), extending `scripts/e2e_check.py`;
- the optional SHOULD FIX wording items SF2–SF8 listed above.

No merges, no real-data spike, no recordings until approved.
