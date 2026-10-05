# Consent Form v1: Independent Reviews

## Round 1 (2026-10-05)

**Reviewed:** `docs/spike/CONSENT_FORM.md` as of commit `e7bd1d5` (after the preparation-review fixes).
**Reviewer:** the `critical-reviewer` agent (read-only, fresh context).
**Verdict:** **Needs changes.** No major rework is needed, but the form is not ready to sign. The main problems are Part D, the scope of withdrawal, and how coercion is handled.
**Status:** the user approved all fixes, #1–16, on 2026-10-05, and they are **applied** in `CONSENT_FORM.md` (#14 in `SPIKE_PLAN.md` §2). Team-specific values were left as blanks, not filled in. The form is still a **draft** and is not approved.

The assistant checked items 1, 2 and 14 against the files and found them accurate.

### Problems

| # | Severity | Section | Problem | Proposed fix |
|---|---|---|---|---|
| 1 | **Blocker** | Part D vs §5 | §5 promises "No machine-translated text spoken in your voice" and no playback "beyond the people listed in 3.4". D1 (develop and test) and D2 (demo, including a viva or expo audience) would break both. | Add to Part D: "If ticked, these uses replace §5's limits for that use only. In development and the demo, your cloned voice will speak Tamil translations drafted by AI and approved by a human reviewer, about [demo topic]." |
| 2 | **Blocker** | §8, D2/D3 | Withdrawal deletes only clips, transcripts and cloned audio. It leaves out: the `demo_reset` database and media snapshot (ADR 0012 §7, which holds the reference clip and cloned previews outside the ADR 0006 purge), the D3 screen recording, speech-to-text outputs, and any VoiceProfile in the system. | §8 item 2: "…and all copies, including the demo reset snapshot, the backup screen recording, transcripts made by speech-to-text, and any copy in the HyperLocalize system." Also state what is **kept**: spike-log lines, file hashes and pseudonymised scores. |
| 3 | Major | §1, Who signs, §9 | Coercion is under-handled. Under SPIKE_PLAN rule 4, if a speaker says no, the cloned voice can drop out of the MVP, so a peer's refusal visibly costs the team. A teammate explains the form, and the faculty countersignature is only recommended. | Add: "If not enough speakers agree, the project uses a stock voice. This is an accepted outcome." Allow at least 24 h between the explanation and signing. Have a non-speaker or the faculty guide explain the form. Make the faculty countersignature required. |
| 4 | Major | 3.4 / 3.6, §9 | Speaker B's clone is played to listeners who know **A** (3.6). Only A's form names those listeners. | Add to §9: "Listeners who know the other speaker (they will hear your clone under 3.6): ____". Name R1 and R2 as well. |
| 5 | Major | 3.1, §5, §3 | The speaker consents to Tamil texts that don't exist yet (TEST_SCRIPT §3 and §6 are still to be written by R1). A repository path means nothing to a non-technical signer. | Sign only after TEST_SCRIPT is frozen. Attach the exact reference, held-out and §6 texts as an appendix that the speaker initials. |
| 6 | Major | §7 | The risks section leaves out: laptop loss or theft (disk encryption is [UNKNOWN]), backups that copy the home folder, expo attendees filming on their phones (D2), Kaggle copies that persist, and being identifiable despite the pseudonym. | Add these risks. Add to §6: "The folder is excluded from all backups; disk encryption: yes / no." |
| 7 | Major | Missing | The form never explains what a "clone" physically is. | "No model is trained on your voice. A 'clone' is only the audio files we generate. Your reference clip is what makes new ones possible, so deleting it stops new clones." Mark this [INFERRED from ADR 0015] until it is checked against the IndicF5 model card. |
| 8 | Major | §8 item 1 | "Immediately" can't be guaranteed: a person has to act on the laptop. | "As soon as the contact receives your request (aim: same day), we stop any processing on the laptop." |
| 9 | Minor | 3.0 | Says the two Tamil raters check transcripts, but TEST_SCRIPT §7 assigns that to "Team". "Laptop only" also clashes with 3.2 and 3.3. | "…listening by team members and R1/R2. With 3.0 alone, nothing leaves the laptop." |
| 10 | Minor | §4 | Gemini and Groq also receive text for the M3 meaning-check, not only for translation. | "for translation and checking tests" |
| 11 | Minor | 3.3 | The statement that ZDR is on has no date or source. | "Turned on by the team (account setting, checked 2026-10-05). We will show you the coverage evidence before sending." |
| 12 | Minor | §6, phone row | Phones keep "Recently deleted" items for up to 30 days. | "…delete it, then empty the phone's recently deleted folder." |
| 13 | Minor | §6, Part D | "End of the spike" is undefined, and "end of the final viva" is an event whose date can slip. | Use fixed dates. Say what is deleted at the Part D end date, and by when. |
| 14 | Minor | Consistency | SPIKE_PLAN §2 says the reference clips are 10–15 s; the form and TEST_SCRIPT say 8–11 s. | Fix SPIKE_PLAN (not a consent change). |
| 15 | Minor | Status row | The form leaves the ethics check to the speaker. | The team asks the faculty guide; record "Institutional ethics approval needed? ___ (asked on ___)". |
| 16 | Minor | Versioning | There is no rule for re-consent if the form changes. | "If this form changes, nothing new happens until you sign the new version." |

**Honesty:** none of the banned words appear. One unverified process claim: 3.5 says the fingerprint "is deleted straight after". Replace it with "is never saved to disk; this is checked when the script is reviewed."

**Blanks to add:** the names of R1 and R2, the other speaker's listeners, the outcome of the ethics check, the disk-encryption answer, the date the ZDR coverage was checked, the spike end date, the demo topic for Part D, and a "copy given to speaker" tick.

**Demo and viva risks:**
- "Your demo reset brings back a revoked speaker's voice. Is revocation real?" (fixed by #2)
- "Did a teammate feel free to refuse?" (fixed by #3)
- "Your form promised no machine text in the clone." (fixed by #1)

**What the reviewer found good:** the Kaggle limits are stated precisely and match ADR 0006 §6; the permissions are separate and not bundled; the form says "pseudonymised, not anonymous"; Groq audio is gated on evidence, and cloned audio never goes to Groq.

---

## Round 2: final review of the revised form (2026-10-06)

**Reviewed:** `CONSENT_FORM.md` as of commit `ecf0116`, after fixes #1–16.
**Reviewer:** the `critical-reviewer` agent (fresh context).
**Verdict:** **Needs changes:** 1 blocker, 4 major, 4 minor.
- Fully fixed: #3, #4 and #8–#16.
- Partly fixed: #1 (inaccurate and overreaching), #2 (incomplete) and #7 (overclaims).
- Fixed, with a small follow-up still needed: #5 and #6.

**Status:** **not applied.** These are changes to consent and to the spike decision rules, so they need the user's approval. The assistant checked P1, P6 and P9 against the files and found them accurate:
- ADR 0013 UC1 runs UC3 and then UC4 as jobs, so cloned previews come before review.
- TEST_SCRIPT §7 puts R1's texts after the freeze.
- SPIKE_PLAN M4 and rule 4 have no outcome for when ECAPA is skipped.

| # | Severity | Section | Problem | Proposed fix |
|---|---|---|---|---|
| P1 | **Blocker** | Part D | "approved by a human reviewer" is inaccurate. Under ADR 0013, cloned previews are generated from AI drafts **before** review, and a Plan A live regeneration plays unreviewed text to the panel. | "Your cloned voice will speak Tamil translations drafted by AI. Until a reviewer checks them they may contain errors, including wrong numbers or a missing 'not'. Unreviewed versions are heard by the team, and in a live demo regeneration by the panel." |
| P2 | Major | Part D | "Replaces the limits in §5" lifts **every** §5 limit, including no commercial use, no face use and nothing in git. | Name exactly what each tick lifts: D1 lifts the machine-text limit only (heard by the team, R1 and R2); D2 lifts the machine-text and playback limits (to the panel and audience); D3 lifts the playback limit (to the panel); D4 lifts the Kaggle limit. Add: "All other §5 limits still apply." |
| P3 | Major | §8 vs §6 | §8 deletes copies that §6 never lists. The golden project (ADR 0012 §2) and export packages are missing, and so is ADR 0006 §7 (downloaded exports can't be recalled). | Add a §6 row for "Part D copies" (location, backup and cloud rules, deletion date). Add the golden project and exports to §8. Add: "Exports copied off the laptop cannot be recalled." |
| P4 | Major | §1 | "Deleting it stops any new clones" overclaims: any clear recording, or the clone itself, can act as a reference, and Kaggle or Groq may hold copies. | "Any clear recording of your voice can be used as a reference. Deleting all your recordings and cloned audio (§8) stops **us** making new clones. Copies outside our control (§6) are not covered." Keep [INFERRED] until the model card is checked. |
| P5 | Major | Part D footnote vs D2 | The footnote says you can revoke in the system, but D2 says the on-stage revocation isn't real. What counts as a real withdrawal is ambiguous, and `demo_reset` reverses revocations made in the system. | Define a real withdrawal: one given to the §8 contact, or a revocation in the system outside a demo. State that after a real withdrawal no reset can bring your voice back. The wording depends on ADR 0020; until the system exists, a team member deletes the copies by hand and logs it. |
| P6 | Minor | Header "When to sign" | A frozen script doesn't make Appendix A final, because R1's Tamil texts come after the freeze. | "Only after the test script is frozen **and** R1's Tamil texts in Appendix A have been checked by R2." Reorder TEST_SCRIPT §7 to match. |
| P7 | Minor | §6 | "Excluded from all backups" is stated before anyone has checked it. | "Excluded from backups (checked on ____ by ____)." |
| P8 | Minor | Appendix A | A speaker who doesn't read Tamil can't really initial Tamil text. | "If you do not read Tamil, an English back-translation is read to you before you initial." |
| P9 | Minor | SPIKE_PLAN P6, M4, rule 4 | P6 says "team member" (the form now allows volunteers) and lists only some permissions. M4 doesn't play B's clone to A's listeners, although 3.6 says it does. Rule 4 has no outcome for when ECAPA is skipped (3.5). | Align P6 and M4. Fix the outcome for a skipped ECAPA run **before any results exist** (user decision). |

**Interim rule proposed by the reviewer:** no demo-reset snapshot or golden project may contain a real speaker's voice until the ADR 0006/0012 change (ADR 0020) is approved.

**What the reviewer found good:** the coercion safeguards are now strong; the Kaggle and Groq limits are stated exactly; 3.0–3.6 are separate ticks with clear dependencies; and the Speaker B listener sets now match.
