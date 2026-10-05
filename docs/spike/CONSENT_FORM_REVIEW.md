# Consent Form v1: Independent Review (2026-10-05)

**Reviewed:** `docs/spike/CONSENT_FORM.md` as of commit `e7bd1d5` (after the preparation-review fixes).
**Reviewer:** the `critical-reviewer` agent (read-only, fresh context).
**Verdict:** **Needs changes.** No major rework is needed, but the form is not ready to sign. The main problems are Part D, the scope of withdrawal, and how coercion is handled.
**Status:** none of the fixes has been applied yet. Changes to consent need the user's approval (CLAUDE.md §11c).

The assistant checked items 1, 2 and 14 against the files and found them accurate. The other items are the reviewer's reading and have not been re-checked yet.

## Problems

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
