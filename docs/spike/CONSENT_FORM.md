# Speaker Consent Form: HyperLocalize Technical Spike

| | |
|---|---|
| **Form ID / version** | `HL-SPIKE-CONSENT` v1 — **DRAFT, not yet approved** (revised after independent review, 2026-10-05) |
| **Implements** | Spike prerequisite P6 (`docs/SPIKE_PLAN.md` §1); consent uses from ADR 0006 §2 |
| **Status of this form** | Written by the project team. **It has not been reviewed by a lawyer or an ethics committee.** If your institution has an ethics or data-protection process, follow it as well; it takes precedence over this form. |
| **Who signs** | Each team member whose voice is recorded for the spike (at least 2 speakers: Speaker A and Speaker B). Speakers must be 18 or older. |
| **Countersigned by** | The faculty guide (recommended; see §9) |

One copy per speaker. Print, fill in, sign. Store the signed copy **outside git** (it contains personal data). Record only the form ID, version, speaker pseudonym and date in the spike log.

---

## 1. What this is about (plain language)

HyperLocalize is an **academic, non-commercial** student project that adapts videos from English into Tamil. Before building the system, we are running a small **technical test ("spike")** to find out which free tools work well enough.

One of the things we test is **voice cloning**: a computer model listens to a short clip of your voice and then produces **Tamil speech that sounds like you**, saying things you never actually said. We need your permission for this, and for a few related steps, listed separately below.

**Taking part is voluntary.** Each permission is optional and separate. **Saying no, or withdrawing later, has no effect on your role, marks or standing in the team.** If you feel pressured, tell the faculty guide (§9).

## 2. What we will record

| Recording | Length | Content |
|---|---|---|
| Test clip (Speaker A only) | 90–120 s | The scripted English health-information text in `docs/spike/TEST_SCRIPT.md` |
| English reference clip | 8–11 s | A fixed English sentence, with its exact transcript |
| Tamil reference clip | 8–11 s | A fixed Tamil sentence written by the project's Tamil rater, with its exact transcript |
| Held-out clip (for comparison only) | 8–11 s | A second fixed English sentence, never used for cloning |

**Audio only.** No video of your face is used in the spike. Nothing you say outside the script is used. Recording is done on the team laptop where possible (see §6 for phone recordings).

## 3. Permissions (tick YES or NO for each)

| # | Permission | What happens if YES | YES | NO |
|---|---|---|---|---|
| 3.0 | **Recording and local processing** | You are recorded. The recordings are processed **on the team laptop only**: speech-to-text with a local model, hand-marking of segment boundaries, and listening by the two Tamil raters (R1, R2) to check transcripts. *Every other permission below needs this one.* | ☐ | ☐ |
| 3.1 | **Voice synthesis** (`voice_synthesis`) | The IndicF5 model creates Tamil speech in your voice from your reference clips, **on the team laptop**. The clone only ever says **human-written, rater-checked Tamil text** listed in `TEST_SCRIPT.md` §6. Machine translations are **never** spoken in your voice. | ☐ | ☐ |
| 3.2 | **Remote voice processing** (`remote_voice_processing`) | **Only if the laptop is too slow:** your reference clips, their transcripts and the Tamil text are uploaded to **Kaggle** (a Google-owned service) as a **private** dataset. The cloned Tamil audio is produced and temporarily stored on Kaggle, then downloaded. See §6 for what deletion on Kaggle does and does not guarantee. | ☐ | ☐ |
| 3.3 | **External transcription** (`external_transcription`) *(Speaker A only)* | Your test-clip audio is sent to **Groq** (a US company) for speech-to-text, to compare against transcription on the laptop. Groq states it does not use inputs for training. **Your audio is sent only if Groq's Zero Data Retention setting can be turned on for our free account. If it cannot, your audio is not sent to Groq at all.** | ☐ | ☐ |
| 3.4 | **Listening tests** | Your real voice and cloned voices are **played in person on the laptop** (no copies handed over) to: R1, R2, up to 4 other named Tamil-speaking listeners, and a few listeners **who know you**, who are asked whether the clone sounds like you. | ☐ | ☐ |
| 3.5 | **Voice comparison score** | A speaker-recognition model (ECAPA-TDNN) compares your real voice (the held-out clip) with cloned voices **on the laptop**. Only the resulting similarity **number** is kept; the voice "fingerprint" it computes is deleted straight after. | ☐ | ☐ |
| 3.6 | **Your clone as a comparison sample** | Your cloned voice is also compared with **another speaker's** real voice, by the model in 3.5 and by that speaker's listeners in 3.4. This is the "different person" check that shows whether cloning really copies a specific voice. | ☐ | ☐ |

**What depends on what:**
- NO to 3.0: you are not recorded.
- NO to 3.1: your voice is not cloned. You can still help with transcription tests only.
- NO to 3.2: your voice is processed only on the laptop, even if that means the cloned-voice test cannot be completed for you.
- NO to 3.3: your audio never leaves the laptop for transcription.
- **Speaker B** is useful for the comparison check only with 3.0, 3.1, 3.5 and 3.6 (3.4 is also needed for the listener check).

*3.4–3.6 are spike-only permissions. They are not consent `use` values in the HyperLocalize system (ADR 0006).*

## 4. Disclosure: Google Gemini (no tick needed, please read)

The **written script text** (not your voice) is sent to **Google's Gemini API free tier** for translation tests. Google's terms say free-tier content **may be used to improve Google's products and train its models, and may be read by human reviewers**. The script is written by the team and contains no personal information about you. **Your audio is never sent to Gemini.**

☐ I have read this disclosure.

## 5. What we will NOT do

- No use of your face or video.
- No commercial use. Some of the models used are licensed for non-commercial use only.
- No playing or publication of your cloned voice beyond the people listed in 3.4.
- No uploading of your recordings to any service other than those named above (Kaggle only if 3.2 is YES; Groq only if 3.3 is YES). **Checking the intelligibility of cloned audio uses a local model on the laptop, not Groq.**
- No committing of your recordings, transcripts or cloned audio to git.
- **No machine-translated text spoken in your voice.** The clone says only the rater-checked Tamil text in `TEST_SCRIPT.md` §6, including versions that write the numbers as digits or as words.

## 6. Storage, retention and deletion

| Item | Where it is kept | Deleted when |
|---|---|---|
| Your recordings and cloned audio | The team laptop only, in a folder outside the git repository and **not inside any cloud-synced folder** (OneDrive, Google Drive and so on). Accessible to the team. | At the end of the spike, and **no later than the expiry date in §8**, unless you agree to Part D |
| A phone copy, if a phone was used to record | The phone, recorded in airplane mode with cloud backup off | Straight after transfer to the laptop by cable. The deletion is logged. |
| Copies on Kaggle (only if 3.2 is YES) | Private Kaggle dataset and notebook output | We run Kaggle's delete commands straight after the results are downloaded, and on withdrawal. **Limits:** a job already running on Kaggle **cannot be stopped** and may finish. **Whether deleting removes its output is not yet verified.** We test this in the spike and will tell you the result. Output produced after you withdraw is **never imported**. What Kaggle keeps internally after deletion is outside our control. |
| Copies at Groq (only if 3.3 is YES) | Groq servers | Sent only with Zero Data Retention on (see 3.3). What Groq keeps internally is outside our control. |
| Ratings and numbers (scores, error counts) | `docs/EVALUATION.md` in the repository | Kept, under your pseudonym "Speaker A" or "Speaker B". **Within the team and the class, the pseudonym may still identify you.** |

**Every deletion is written down in the spike log** (what, where, when, by whom). Short-lived temporary files on the laptop are deleted when each run ends.

**Test of the withdrawal mechanism.** The spike tests whether a withdrawal really stops processing, by **simulating** one on your recordings (`SPIKE_PLAN.md` M9). This simulation is **not** your withdrawal and does not end your consent. If it shows that Kaggle keeps output after deletion, we will tell you.

## 7. Risks

- A cloned voice could be misused if it leaked, for example to make it sound as if you said something you did not. We reduce this risk by keeping cloned audio on one laptop, playing it only in person, and deleting it at the end of the spike.
- Listeners who know you will hear synthetic speech in your voice.

## 8. Withdrawing consent

You can withdraw **any or all** permissions **at any time, without giving a reason**, by telling: **[name, phone / email — to be filled in]**, or the faculty guide (§9).

When you withdraw, we will within **[N, e.g. 2] working days**:
1. stop any processing of your voice **on the laptop**. On Kaggle, a job already running may finish, but its output is never imported;
2. delete your recordings, any cloned audio of you, and run Kaggle's delete commands for any copies there (with the limits in §6);
3. record the deletions in the spike log and tell you when they are done.

Scores already in `docs/EVALUATION.md` stay, under your pseudonym.

**This consent expires on [date — PROPOSED: 31 December 2026].** After that date, nothing in this form allows further use of your voice, **except** the uses you tick in Part D, and only until Part D's own end date.

## Part D (optional): use after the spike

Each use is a separate tick. Part D extends the expiry in §8 **for the ticked uses only**, until **[date, e.g. the end of the final viva]**.

| Use after the spike | YES | NO |
|---|---|---|
| D1. Keep my recordings to **develop and test** HyperLocalize on the team laptop | ☐ | ☐ |
| D2. Play my real and cloned voice in the **live demo** to the evaluation panel | ☐ | ☐ |
| D3. Include my cloned voice in the **backup screen recording** of the demo, kept by the team and shown only to the panel | ☐ | ☐ |
| D4. Kaggle processing (as in 3.2) during development | ☐ | ☐ |

*If you tick any of D1–D4, the HyperLocalize system will also record your consent in its own consent records, where you can view and revoke it. This form does not replace that.*

---

## 9. Signatures

| | Speaker |
|---|---|
| Speaker name | |
| Pseudonym (assigned by team) | Speaker A / Speaker B |
| Native Tamil reader? (for the Tamil reference clip) | Yes / No |
| Signature | |
| Date | |
| Form version | `HL-SPIKE-CONSENT` v1 |
| Team member who explained the form | |

| | Faculty guide (recommended) |
|---|---|
| Name | |
| Contact (escalation for pressure or withdrawal) | |
| Signature and date | |
