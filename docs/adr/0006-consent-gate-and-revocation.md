# ADR 0006: Consent gate, checks at each stage boundary, revocation cascade

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review; **revised again 2026-10-05 for the zero-budget runtimes: local CPU and Kaggle batch**). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §3.4, §6.8; CLAUDE.md §5; ADRs 0005, 0019

## Context

Consent must be enforced in the backend before any operation that uses a Speaker / Identity Owner's identity. Revocation must actually stop things, including **jobs that are already running** (CLAUDE.md §5). The live revocation demo must work **mid-job**.

After the zero-budget decision, cloned-voice synthesis (IndicF5) runs in one of two places:
- **local CPU:** an inference subprocess on the laptop. Slow, but fully under our control.
- **Kaggle GPU batch:** a private dataset plus a pushed kernel. Fast, but **the Kaggle CLI has no cancel command** for a running kernel, only `kernels delete` and `datasets delete`.

A "voice profile" is now **our own stored reference clip plus its transcript**. No third-party voice-clone object exists, except the temporary copy uploaded to Kaggle for a batch run.

Faces are not processed (Q5). Q6 allows external processing of the team's own voices.

## Options Considered

| Criterion | UI-only checks | Check once at job claim | Gate at every stage boundary + locked check-and-save + runtime-specific stop | Signed capability tokens per job |
|---|---|---|---|---|
| Meets CLAUDE.md §5 | No | No | Yes | Yes |
| Stops a running local job | No | No | **Yes: the subprocess is killed** | Needs the same mechanism |
| Remote batch (Kaggle) | — | No | **Output never accepted; remote inputs and outputs deleted** | Same limits |
| Race between revoke and save | — | Present | Closed by row locks | Needs the same locking |
| Explainability | — | High | High | Medium |

## Decision

**1. One gate.** `require_active_consent(identity_owner, use, project, language)` in the `identity` app is the only code that decides whether identity may be used. It also checks the job's `cancel_requested` flag. It returns a `ConsentCheck`, which identity-using methods require (ADR 0005).

**2. What counts as identity use.** Using the reference clip to synthesise speech in `CLONED_VOICE` mode (locally or on Kaggle), uploading the reference clip to Kaggle, rendering or mixing a scene with cloned audio, approving a snapshot containing it, exporting it, and serving it. `STOCK_VOICE` and `SUBTITLES_ONLY` don't use identity.

**3. Checkpoints, one at every stage boundary.**

| # | Stage boundary | On failure |
|---|---|---|
| CP1 | API request that would use identity | Refuse; audit `CONSENT_DENIED` |
| CP2 | Job claim (same transaction) | `CANCELLED` |
| CP3 | **Before the reference clip leaves the laptop** (Kaggle dataset upload) | `CANCELLED`; nothing uploaded |
| CP4 | **Before synthesis.** Local: before *each segment*. Kaggle: before dispatching the batch. | Stop; `CANCELLED` |
| CP5 | Saving synthesised audio, **including importing Kaggle output** (locked) | Discard; delete temp files |
| CP6 | **Before scene render / mix** | `CANCELLED` |
| CP7 | Saving the rendered scene (locked) | Discard |
| CP8 | Approval (every consent version in the snapshot still active) | Refuse approval |
| CP9 | **Before export build, and when saving the export (locked)** | `CANCELLED` |
| CP10 | Serving previews and export downloads | `410 Gone`, with an explanation |

**4. Race-free saving.**
- Revocation and every save checkpoint (CP5, CP7, CP9) run `select_for_update()` on the same Consent row. Django's ORM doesn't provide `FOR SHARE` (verified in the Django 6.1 docs).
- The save re-checks ACTIVE and inserts the artefact with its `consent_id` and `consent_version` in the same transaction.
- So either the artefact is saved first and the revocation that follows quarantines it, or the revocation goes first and the save aborts.

**5. Revocation transaction.** Write a new REVOKED consent version. Then:
- cancel QUEUED jobs;
- set `cancel_requested` on RUNNING and DISPATCHED jobs;
- quarantine every artefact recorded under the consent;
- invalidate affected approvals;
- mark affected exports `CONSENT_REVOKED`;
- queue a `purge_identity_data` job (delete the local reference clip, plus Kaggle datasets and kernels that hold it);
- write the audit record.

**6. How a running job stops, by runtime.**

| Runtime | How it stops | Time to stop | What may remain outside our control |
|---|---|---|---|
| **Local inference subprocess** (IndicF5 on CPU, MMS-TTS, Parler-TTS) | The worker checks `cancel_requested` about once a second while it waits on the subprocess. On revocation it **kills the subprocess**, deletes temp audio, and marks the job `CANCELLED (CONSENT_REVOKED)`. | Seconds (measured in spike M9) | Nothing |
| **Kaggle batch** (IndicF5 on GPU) | The worker stops polling, marks the job `CANCELLED (CONSENT_REVOKED)`, and runs `kaggle kernels delete` and `kaggle datasets delete`. Its output is **never imported**: CP5 fails under the lock even if a late import is attempted. | Immediate on our side. **Whether `kernels delete` stops remote compute is [UNVERIFIED]** (spike M9). | Remote compute may run to completion. Its output is deleted with the kernel. Kaggle's own retention of deleted data is beyond our control and stated as such. |
| **Hosted API call** (e.g. a stock voice from a free tier) | Not identity use, so not subject to this gate. A cancelled job discards in-flight results. | One call | — |

After any stop:
- the job is never retried;
- segments saved earlier are quarantined;
- the scene becomes `NEEDS_REGENERATION`;
- a fallback render (`STOCK_VOICE` / `SUBTITLES_ONLY`) is queued that **requires review again**;
- the Localization Manager sees a notice;
- any deletion that hasn't succeeded yet shows as **"deletion pending"**, never as done.

**7. Exports already downloaded cannot be recalled.** This is stated in the UI and the docs.

**8. Consent evidence.** Each Consent version stores who granted it, when, the scope, the **named processors** (Groq for transcription audio, Kaggle for reference audio and cloned output, Google Gemini free tier for script text, with its training and human-review terms), and the signed consent form.

**9. Demo safety.**
- The live revocation demo uses a **local** cloned-voice job. Local CPU synthesis is slow, so revocation lands mid-job without timing tricks, and killing the subprocess makes the stop visible within seconds.
- A **deterministic integration test** covers every checkpoint, using a barrier in `MockSpeechSynthesisProvider`.
- A **subprocess-kill test** and a **Kaggle-path test** use a mocked Kaggle CLI: revoke while DISPATCHED, then assert no import, deletion commands issued, and the right audit entries.
- A **concurrency test** covers revoke vs. save in both orders.
- A **test matrix** covers every identity operation × consent state.

## Consequences

- **+** Locally, revocation stops synthesis within seconds, which is stronger than before because we control the process.
- **+** No third-party voice-clone object exists, so deletion is mostly ours to do and verify.
- **−** Kaggle runs can't be cancelled. The guarantee there is "nothing produced after revocation is ever accepted, and remote copies are deleted", **not** "remote compute stops". It must be described exactly like this.
- **−** A missing checkpoint is a bypass. Mitigated by the required `ConsentCheck` parameter and one test per checkpoint.
- Retention for quarantined media: deleted after 7 days [PROPOSED default].
- **Viva in 2 minutes:** "One function decides consent, at every stage boundary. Revocation and saving take the same lock. A local synthesis job is killed within seconds. A Kaggle job can't be cancelled, so its output is refused at import and its remote files are deleted, and we say exactly that."
