# Speaker Consent Form: HyperLocalize Technical Spike

| | |
|---|---|
| **Form ID / version** | `HL-SPIKE-CONSENT` v1 — **DRAFT, not yet approved** (revised after two independent reviews and preparation-review fixes, 2026-10-05; round-2 fixes P1–P8 applied 2026-10-06) |
| **Implements** | Spike prerequisite P6 (`docs/SPIKE_PLAN.md` §1); consent uses from ADR 0006 §2 |
| **Status of this form** | Written by the project team. **It has not been reviewed by a lawyer or an ethics committee.** The team asks the faculty guide whether institutional ethics or data-protection approval is needed, and records the answer in §9. If it is needed, it takes precedence over this form. |
| **Who signs** | Each speaker (team member or volunteer) whose voice is recorded for the spike (at least 2 speakers: Speaker A and Speaker B). Speakers must be 18 or older. |
| **Countersigned by** | The faculty guide (**required**; see §9). The speaker keeps a copy of the signed form. |
| **When to sign** | Only **after** the test script is frozen **and** R1's Tamil texts in Appendix A have been checked by R2, so that every text in Appendix A is final. At least **24 hours** must pass between the form being explained to you and you signing it. The form is explained by the faculty guide or by a team member who is **not** a speaker. |
| **If this form changes** | Nothing new happens with your voice until you have signed the new version. |

One copy per speaker. Print, fill in, sign. Store the signed copy **outside git** (it contains personal data). Record only the form ID, version, speaker pseudonym and date in the spike log (`~/hl-spike-media/spike-log.md` on the team laptop: append-only, timestamped, no names and no recorded content).

---

## 1. What this is about (plain language)

HyperLocalize is an **academic, non-commercial** student project that adapts videos from English into Tamil. Before building the system, we are running a small **technical test ("spike")** to find out which free tools work well enough.

One of the things we test is **voice cloning**: a computer model listens to a short clip of your voice and then produces **Tamil speech that sounds like you**, saying things you never actually said. We need your permission for this, and for a few related steps, listed separately below.

**What a "clone" is.** No model is trained on your voice. Each time, the model is given your short reference clip and its transcript, and it produces new audio files. A "clone" is only those generated audio files. **Any clear recording of your voice can be used as a reference**, including the clone itself. Deleting all your recordings and cloned audio (§8) stops **us** making new clones. Copies outside our control (§6: Kaggle, Groq) are not covered. *[INFERRED from ADR 0015, which describes IndicF5 as prompt-based. To be checked against the IndicF5 model card before signing.]*

**Taking part is voluntary.** Each permission is optional and separate. **Saying no, or withdrawing later, has no effect on your role, marks or standing in the team.** If not enough speakers agree, the project uses a stock (non-cloned) voice instead. **This is an accepted outcome.** If you feel pressured, tell the faculty guide (§9).

## 2. What we will record

| Recording | Length | Content |
|---|---|---|
| Test clip (Speaker A only) | 90–120 s | The scripted English health-information text (Appendix A) |
| English reference clip | 8–11 s | A fixed English sentence, with its exact transcript |
| Tamil reference clip | 8–11 s | A fixed Tamil sentence written by the project's Tamil rater, with its exact transcript |
| Held-out clip (for comparison only) | 8–11 s | A second fixed English sentence, never used for cloning |

The exact text of every recording is in **Appendix A**, which is attached to this form and initialled by you.

**Audio only.** No video of your face is used in the spike. Nothing you say outside the script is used. Recording is done on the team laptop where possible (see §6 for phone recordings).

## 3. Permissions (tick YES or NO for each)

| # | Permission | What happens if YES | YES | NO |
|---|---|---|---|---|
| 3.0 | **Recording and local processing** | You are recorded. The recordings are processed **on the team laptop only**: speech-to-text with a local model, and listening by team members and the two Tamil raters (R1, R2) to check transcripts and hand-mark segment boundaries. **With 3.0 alone, nothing leaves the laptop.** *Every other permission below needs this one.* | ☐ | ☐ |
| 3.1 | **Voice synthesis** (`voice_synthesis`) | The IndicF5 model creates Tamil speech in your voice from your reference clips, **on the team laptop**. During the spike, the clone only ever says the **human-written, rater-checked Tamil text** in Appendix A. Machine translations are **never** spoken in your voice during the spike (Part D covers uses after the spike). | ☐ | ☐ |
| 3.2 | **Remote voice processing** (`remote_voice_processing`) | **Only if the laptop is too slow:** your reference clips, their transcripts and the Tamil text are uploaded to **Kaggle** (a Google-owned service) as a **private** dataset. The cloned Tamil audio is produced and temporarily stored on Kaggle, then downloaded. See §6 for what deletion on Kaggle does and does not guarantee. | ☐ | ☐ |
| 3.3 | **External transcription** (`external_transcription`) *(Speaker A only)* | Your test-clip audio is sent to **Groq** (a US company) for speech-to-text, to compare against transcription on the laptop. Groq states it does not use inputs for training. Groq's Zero Data Retention setting was turned on by the team (an account setting; reported 2026-10-05). **We will show you the dated evidence of what it covers before sending anything.** **Your audio is sent only after we have confirmed, with dated evidence, that this setting also covers Groq's speech-to-text service. If it does not, your audio is not sent to Groq at all.** | ☐ | ☐ |
| 3.4 | **Listening tests** | Your real voice and cloned voices are **played in person on the laptop** (no copies handed over) to: R1, R2, up to 4 other Tamil-speaking listeners **named in §9**, and listeners **who know you, also named in §9**, who are asked whether the clone sounds like you. If you say YES to 3.6, your clone is also played to **the listeners who know the other speaker**, named in §9. No one else listens. Listeners are asked not to record anything. | ☐ | ☐ |
| 3.5 | **Voice comparison score** | A speaker-recognition model (ECAPA-TDNN) compares your real voice (the held-out clip) with cloned voices **on the laptop**. Only the resulting similarity **number** is kept. The voice "fingerprint" it computes is never saved to disk; this is checked when the comparison script is reviewed. **If the model cannot run on the laptop, this score is skipped; it is never moved elsewhere.** | ☐ | ☐ |
| 3.6 | **Your clone as a comparison sample** | Your cloned voice is also compared with **another speaker's** real voice, by the model in 3.5 and by the listeners who know that speaker (named in §9). This is the "different person" check that shows whether cloning really copies a specific voice. | ☐ | ☐ |

**What depends on what:**
- NO to 3.0: you are not recorded.
- NO to 3.1: your voice is not cloned. **Speaker A** can still help with transcription tests only. **Speaker B** records no test clip, so for B a NO to 3.1 means B is not recorded at all.
- NO to 3.2: your voice is processed only on the laptop, even if that means the cloned-voice test cannot be completed for you.
- NO to 3.3: your audio never leaves the laptop for transcription.
- **Speaker B** is useful for the comparison check only with 3.0, 3.1, 3.5 and 3.6 (3.4 is also needed for the listener check).

*3.4–3.6 are spike-only permissions. They are not consent `use` values in the HyperLocalize system (ADR 0006).*

## 4. Disclosure: script text sent to Google Gemini and Groq (no tick needed, please read)

The **written script text** (not your voice) is sent to **Google's Gemini API free tier** and to **Groq's hosted language models** for translation and checking tests. Groq states it does not use inputs for training. Google's terms say free-tier content **may be used to improve Google's products and train its models, and may be read by human reviewers**. The script is written by the team and contains no personal information about you. **Your audio is never sent to Gemini.**

☐ I have read this disclosure.

## 5. What we will NOT do

These limits apply to the spike. Part D can change them **only for the uses you tick there**.

- No use of your face or video.
- No commercial use. Some of the models used are licensed for non-commercial use only.
- No playing or publication of your cloned voice beyond the people listed in 3.4.
- No uploading of your recordings to any service other than those named above (Kaggle only if 3.2 is YES; Groq only if 3.3 is YES). **Checking the intelligibility of cloned audio uses a local model on the laptop, not Groq.**
- No committing of your recordings, transcripts or cloned audio to git.
- **No machine-translated text spoken in your voice.** The clone says only the rater-checked Tamil text in Appendix A, including versions that write the numbers as digits or as words.

## 6. Storage, retention and deletion

| Item | Where it is kept | Deleted when |
|---|---|---|
| Your recordings and cloned audio | The team laptop only, in the folder `~/hl-spike-media/`, which is outside the git repository and **not inside any cloud-synced folder** (OneDrive, Google Drive and so on). Accessible to the team. **The folder is excluded from backups (checked on ______ by ______).** Laptop disk encryption: ☐ Yes ☐ No *(filled in by the team)*. | At the end of the spike, on **[spike end date — to be filled in]**, and **no later than the expiry date in §8**, unless you agree to Part D |
| A phone copy, if a phone was used to record | The phone, recorded in airplane mode with cloud backup off | Straight after transfer to the laptop by cable: the recording is deleted, **then the phone's "recently deleted" folder is emptied**. The deletion is logged. |
| Copies on Kaggle (only if 3.2 is YES) | Private Kaggle dataset and notebook output | We run Kaggle's delete commands straight after the results are downloaded, and on withdrawal. **Limits:** a job already running on Kaggle **cannot be stopped** and may finish. **Whether deleting removes its output is not yet verified.** We test this in the spike and will tell you the result. Output produced after you withdraw is **never imported**. What Kaggle keeps internally after deletion is outside our control. |
| Copies at Groq (only if 3.3 is YES) | Groq servers | Sent only with Zero Data Retention on (see 3.3). What Groq keeps internally is outside our control. |
| Part D copies (only if you tick D1–D4) | The team laptop only: `~/hl-spike-media/` and the HyperLocalize system's media storage on the same laptop, including the demo seed copies and export packages. The golden (pre-prepared) demo project uses stock voices only and holds no copy of your voice. Same rules as above: outside git, not in any cloud-synced folder, excluded from backups. The backup screen recording (D3) is kept in the same folder. Kaggle copies only if D4 is YES, with the limits above. | On Part D's fixed end date, within the same number of working days as §8 item 2, or earlier if you withdraw |
| Ratings and numbers (scores, error counts) | `docs/EVALUATION.md` in the repository | Kept, under your pseudonym "Speaker A" or "Speaker B". This is **pseudonymised, not anonymous**: teammates and examiners may know who Speaker A is, and scores in git history stay there. |

**Every deletion is written down in the spike log** (what, where, when, by whom). Short-lived temporary files on the laptop are **designed** to be deleted when each run ends. This is checked in the withdrawal test below, and logged after each run.

**Test of the withdrawal mechanism.** The spike tests whether a withdrawal really stops processing, by **simulating** one on your recordings (`SPIKE_PLAN.md` M9). This simulation is **not** your withdrawal and does not end your consent. If it shows that Kaggle keeps output after deletion, we will tell you.

## 7. Risks

- A cloned voice could be misused if it leaked, for example to make it sound as if you said something you did not. We reduce this risk by keeping cloned audio on one laptop, playing it only in person, and deleting it at the end of the spike.
- Listeners who know you will hear synthetic speech in your voice.
- **Laptop loss or theft:** anyone who gets the laptop could get your recordings. Whether the disk is encrypted is stated in §6.
- **Backups:** a backup of the laptop's home folder could copy your recordings. The spike folder is to be excluded from backups; the check is recorded in §6.
- **Kaggle (only if 3.2 or D4 is YES):** copies may stay on Kaggle after we delete them (see §6).
- **Live demo audiences (only if D2 is YES):** people in a viva or expo audience could record the demo on their phones. We cannot prevent this.
- **The pseudonym does not hide you from people who know the team:** teammates, listeners and examiners may know who Speaker A or Speaker B is.

## 8. Withdrawing consent

You can withdraw **any or all** permissions **at any time, without giving a reason**, by telling: **[name, phone / email — to be filled in]**, or the faculty guide (§9).

When you withdraw:
1. **As soon as the contact receives your request (aim: the same day):** we stop any processing of your voice **on the laptop**. On Kaggle, a job already running may finish, but its output is never imported.
2. **Within [N, e.g. 2] working days:** we delete your test clip (Speaker A), reference and held-out clips, their transcripts, any cloned audio of you, **and all copies**, including the demo seed copies, export packages, the backup screen recording, transcripts made by speech-to-text, and any copy in the HyperLocalize system. We run Kaggle's delete commands for any copies there (with the limits in §6). **Audio already sent to Groq cannot be recalled by us. Exports copied off the laptop cannot be recalled either.**
3. We record the deletions in the spike log and tell you when they are done.

**What is kept after withdrawal:** the spike-log lines (pseudonyms, file names, durations and file hashes; no audio, transcripts or names) and the scores already in `docs/EVALUATION.md`, under your pseudonym.

**This consent expires on [date — PROPOSED: 31 December 2026].** After that date, nothing in this form allows further use of your voice, **except** the uses you tick in Part D, and only until Part D's own end date.

## Part D (optional): use after the spike

Each use is a separate tick. Part D extends the expiry in §8 **for the ticked uses only**, until **[fixed date — to be filled in]**. On that date, everything kept under Part D is deleted within the same number of working days as in §8 item 2, and the deletion is logged.

**Each tick lifts only the §5 limits named here:**
- **D1** lifts the "no machine-translated text" limit only. The cloned audio is heard by the team, R1 and R2.
- **D2** lifts the "no machine-translated text" limit and the playback limit, for the evaluation panel, the viva or expo audience, and the team's demo rehearsals.
- **D3** lifts the playback limit, for the evaluation panel only.
- **D4** lifts the Kaggle limit (as in 3.2) during development.

**D2 needs D1.** The demo is built from a development copy of your recordings, so D2 counts only if you also tick D1. If you tick D2 without D1, D2 is treated as NO.

**All other §5 limits still apply**, including no face or video, no commercial use and nothing in git.

**What your cloned voice will say.** Your cloned voice will speak Tamil translations drafted by AI, about **[demo topic — to be filled in]**. Until a reviewer checks them, they may contain errors, including wrong numbers or a missing "not". Unreviewed versions are heard by the team, and, in a live demo regeneration, by the panel.

**Interim limit.** Until the team's demo-reset design is approved, your voice is **not** put into any demo seed or golden (pre-prepared) demo project. Under the proposed design, the golden project uses stock voices only.

| Use after the spike | YES | NO |
|---|---|---|
| D1. Keep my recordings to **develop and test** HyperLocalize on the team laptop | ☐ | ☐ |
| D2. Play my real and cloned voice in the **live demo and its team rehearsals**, including the live consent-revocation demo, to the evaluation panel and any viva or expo audience. *A revocation inside a project marked* Demo rehearsal*, on stage or in a team rehearsal, is a demonstration; it does not end your real consent.* | ☐ | ☐ |
| D3. Include my cloned voice in the **backup screen recording** of the demo, kept on the team laptop (outside git and cloud sync) and shown only to the panel | ☐ | ☐ |
| D4. Kaggle processing (as in 3.2) during development | ☐ | ☐ |

*If you tick any of D1–D4, the HyperLocalize system will also record your consent in its own consent records, where you can view and revoke it. This form does not replace that.*

**What counts as a real withdrawal.** In the HyperLocalize system:
- **Revoking inside a project marked *Demo rehearsal*** (on stage or in a team rehearsal) is a demonstration, **not** a withdrawal.
- **Revoking inside a normal project** ends the use of your voice **in that project only**.
- **To withdraw a Part D use, or everything**, untick that use or press *Withdraw* on your consent page, or tell the §8 contact or the faculty guide. This is a real withdrawal: §8 then applies to that use, or to everything.

Adding a use back later needs a new signed form. After a real withdrawal, the team will not use any demo reset to bring your voice back. *The system's support for this is proposed (ADR 0020) and not yet approved or built. Until it exists, a team member deletes the copies by hand (§8) and logs each deletion in the spike log.*

---

## 9. Signatures

| | Speaker |
|---|---|
| Speaker name | |
| Pseudonym (assigned by team) | Speaker A / Speaker B |
| I confirm I am **18 or older** | ☐ Yes |
| Native Tamil reader? (for the Tamil reference clip) | Yes / No |
| Permission 3.4: the Tamil raters | R1: ______ R2: ______ |
| Permission 3.4: the up to 4 named Tamil-speaking listeners (not R1 or R2) | 1. ______ 2. ______ 3. ______ 4. ______ |
| Permission 3.4: listeners who know you (names) | ______ |
| Permission 3.6: listeners who know the other speaker (they will hear your clone) | ______ |
| Appendix A initialled (test script version: ______) | ☐ Yes |
| Signature | |
| Date | |
| Form version | `HL-SPIKE-CONSENT` v1 |
| Person who explained the form (faculty guide, or a team member who is not a speaker) | |
| Date the form was explained (signing must be at least 24 hours later) | |
| Copy of the signed form given to the speaker | ☐ Yes |
| Withdrawal date (if withdrawn) and what was withdrawn | |

| | Faculty guide (**required**) |
|---|---|
| Name | |
| Contact (escalation for pressure or withdrawal) | |
| Institutional ethics approval needed? | ☐ Yes ☐ No (asked on ______) |
| Signature and date | |

---

## Appendix A: exact texts (attached at signing, initialled by the speaker)

Filled in from the **frozen** `docs/spike/TEST_SCRIPT.md`. Do not sign until every item below is final.

**If you do not read Tamil**, an English back-translation of each Tamil item is read to you before you initial it.

| Item | Text | Speaker's initials |
|---|---|---|
| Test script (Speaker A only): the full English text | *(attach the frozen script, version ______)* | |
| English reference sentence (cloning input) | | |
| Tamil reference sentence (cloning input, written by R1) | | |
| Held-out sentence (comparison only, never used for cloning) | | |
| The Tamil texts the clone will say (TEST_SCRIPT §6), with numbers as digits and as words | *(attach)* | |
