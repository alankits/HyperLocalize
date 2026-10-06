# ADR 0006: Consent gate, checks at each stage boundary, revocation cascade

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-04; revised 2026-10-05: ADR review, zero-budget runtimes, and **independent review, which found a critical locking flaw, now fixed**. **Amended 2026-10-06 by ADR 0020** (§1 gate, §4 locked saves, §5 cascade scope, purge and expiry; standing Part D grant in §8).
**Source:** `docs/PHASE0_DISCOVERY.md` §3.4; CLAUDE.md §5; ADRs 0003, 0005, 0014, 0019

## Context

Consent must be enforced in the backend before any operation that uses a Speaker / Identity Owner's identity. Revocation must actually stop things, including **jobs that are already running** (CLAUDE.md §5). The live revocation demo must work **mid-job**.

Identity-related processing now happens in three places:
- **local CPU:** an inference subprocess that we can kill;
- **Kaggle GPU batch:** the Kaggle CLI has **no cancel command**, only `kernels delete` and `datasets delete`;
- **optional external transcription:** Groq, if enabled (ADR 0017). That is the source speaker's audio leaving the laptop.

Consent records are **versioned**: each change inserts a new Consent row (ADR 0014).

## Options Considered

| Criterion | UI-only checks | Check once at job claim | Gate at every stage boundary + locked check-and-save + runtime-specific stop | Signed capability tokens per job |
|---|---|---|---|---|
| Meets CLAUDE.md §5 | No | No | Yes | Yes |
| Stops a running local job | No | No | Yes: subprocess killed | Needs the same mechanism |
| Race between revoke and save | — | Present | Closed by locking a stable row (§4) | Needs the same locking |
| Explainability | — | High | High | Medium |

## Decision

**1. One gate.** `require_active_consent(identity_owner, use, project, language, job=None)`. It returns a `ConsentCheck` (consent id + version) only if:
- the **latest** Consent version for that owner and scope is ACTIVE;
- it is not expired (`expires_at` is in the future);
- it covers the use, project and language;
- if a `job` is given, its `cancel_requested` flag is not set;
- *(amended by ADR 0020, 2026-10-06)* the IdentityOwner is not withdrawn (`withdrawn_at` is not set);
- *(amended by ADR 0020, 2026-10-06)* the version has a parent `STANDING_PART_D` version, and the owner's **latest** standing version is ACTIVE, not expired, and contains the Part D use the project needs (`STANDARD`: D1; `DEMO_REHEARSAL`: D1 and D2; `remote_voice_processing`: D4);
- *(amended by ADR 0020, 2026-10-06)* the version is still **within** that latest standing version (uses, languages, processors, `expires_at`).

Identity-using methods require a `ConsentCheck` (ADR 0005).

**2. Uses** (the `use` values):

| Use | Meaning |
|---|---|
| `voice_synthesis` | Synthesise speech in `CLONED_VOICE` mode, locally or on Kaggle. This also covers rendering, approving, exporting and serving artefacts that contain it. |
| `remote_voice_processing` | Upload the reference clip to Kaggle |
| `external_transcription` | Send source audio to an external ASR (Groq). The MVP default is local transcription, which needs no such consent (ADR 0017). |

`STOCK_VOICE` and `SUBTITLES_ONLY` don't use identity.

**3. Checkpoints, one at every stage boundary.**

| # | Stage boundary | On failure |
|---|---|---|
| CP0 | **Before source audio leaves the laptop** (external ASR only): every IdentityOwner linked to the project must have `external_transcription` consent naming that processor, **and** the project's `allow_external_audio` policy must be on. Otherwise the chain uses local ASR. | Local ASR is used; audited |
| CP1 | API request that would use identity | Refuse; audit `CONSENT_DENIED` |
| CP2 | Job claim (same transaction) | `CANCELLED` |
| CP3 | Before the reference clip is uploaded to Kaggle | `CANCELLED`; nothing uploaded |
| CP4 | **Before synthesis.** Local: before *each segment*. Kaggle: before dispatching the batch. | Stop; `CANCELLED` |
| CP5 | Saving a `SynthesisedSegment`, including Kaggle output imports (locked) | Discard; delete temp files |
| CP6 | **Before scene render / mix** | `CANCELLED` |
| CP7 | Saving a `RenderedScene` (locked) | Discard |
| CP8 | Approval: every consent version in the snapshot is still the latest and ACTIVE | Refuse approval |
| CP9 | **Before export build, and when saving the export (locked)** | `CANCELLED` |
| CP10 | Serving previews and export downloads | `410 Gone`, with an explanation |

**4. Race-free saving: lock the person, not the consent version.** *(Fixed after independent review.)* The previous design locked "the Consent row". But revocation **inserts a new row**, so a save that locked the old version could still see it as ACTIVE.
- Revocation and every save checkpoint (CP5, CP7, CP9) run `select_for_update()` on the **`IdentityOwner` row**, which is stable and always the same row. This is the first lock in the global lock order (ADR 0003).
- Under that lock, a save re-reads the **latest** Consent version for the scope. It saves the artefact only if that version is ACTIVE, not expired, **and the same version as the job's `ConsentCheck`**.
- So either the save commits first and the revocation that follows quarantines the artefact, or the revocation commits first and the save sees a newer REVOKED version and aborts.
- Test: a save attempted after revocation that still carries version N must be refused.
- *(amended by ADR 0020, 2026-10-06)* Under the same lock, the save also runs the full §1 gate (withdrawal and the standing-grant conditions), so a save that commits after a narrowing or withdrawal is refused.

**5. Revocation transaction** (under the IdentityOwner lock). Insert a new REVOKED Consent version. Then:
- cancel QUEUED jobs;
- set `cancel_requested` on RUNNING and DISPATCHED jobs;
- quarantine every `SynthesisedSegment` and `RenderedScene` recorded under a Consent version **in the revoked scope** (same owner, use and project); other projects of the same owner are untouched *(amended by ADR 0020, 2026-10-06)*;
- invalidate affected approvals;
- mark affected exports `CONSENT_REVOKED`;
- queue `purge_identity_data`;
- write the audit record.

**Purge** (runs **immediately**; no 7-day wait, *changed after independent review*):
- deletes the quarantined cloned audio, the audio and video files of quarantined `RenderedScene`s, the package files of exports marked `CONSENT_REVOKED` (status `PURGED`), the reference clip of each VoiceProfile whose consent is in the revoked scope, and every `RemoteCopy` of those VoiceProfiles on Kaggle *(amended by ADR 0020, 2026-10-06)*;
- keeps only hashes and identifiers for audit;
- shows any deletion that hasn't succeeded yet as **"deletion pending"**, retries it, and audits it.

**Expiry:** a periodic sweep in the `default` lane runs the same cascade for consents whose `expires_at` has passed. *(amended by ADR 0020, 2026-10-06)* When an owner's standing Part D grant expires, the sweep runs ADR 0020's narrowing procedure (to nothing, reason `EXPIRED`), which also purges the owner's `OfflineCopy` files.

**Narrowing and withdrawal** *(amended by ADR 0020, 2026-10-06)*. Narrowing the standing grant (uses, Part D uses, languages, processors, or an earlier `expires_at`), or withdrawing entirely, goes through ADR 0020 §5's single narrowing procedure. It runs this cascade on every project scope that no longer passes the gate, and marks the matching `OfflineCopy` rows for deletion. A revocation inside a `DEMO_REHEARSAL` project is a demonstration: it affects only that project, and the next `demo_reset` derives a fresh grant.

**6. How a running job stops, by runtime.**

| Runtime | How it stops | Time to stop | What may remain outside our control |
|---|---|---|---|
| **Local inference subprocess** | The worker checks the flag and the gate about once a second and **kills the subprocess**. Temp audio is deleted. The job ends `CANCELLED (CONSENT_REVOKED)`. | TARGET: seconds; to be measured in spike M9 | Nothing |
| **Kaggle batch** | Polling stops. The job ends `CANCELLED (CONSENT_REVOKED)`. `kaggle kernels delete` and `kaggle datasets delete` are run. Output is **never imported**: CP5 fails under the lock. | Immediate on our side | Remote compute may run to completion. **Whether `kernels delete` stops it, and whether it removes the kernel's output, are both [UNVERIFIED]** (spike M9). Kaggle's retention after deletion is outside our control. |

After any stop:
- the job is never retried;
- segments saved earlier are quarantined, then purged;
- the scene becomes `NEEDS_REGENERATION`;
- a fallback render (`STOCK_VOICE` / `SUBTITLES_ONLY`) is queued and **requires review again**;
- the Localization Manager sees a notice.

**7. Exports already downloaded cannot be recalled.** This is stated in the UI and the docs.

**8. Consent evidence.** Each Consent version stores who granted it, when, the scope, the uses, the **named processors** (Kaggle for reference audio and cloned output; Google Gemini free tier for script text only, with its training and human-review terms; Groq **only if** `external_transcription` is granted), and the signed consent form. *(amended by ADR 0020, 2026-10-06)* Every project version also references the owner's `STANDING_PART_D` version as its parent and is no wider than it; widening the standing grant needs a new signed paper form ID as evidence.

**9. Demo safety.**
- **Main path:** the live revocation demo uses a **local** cloned-voice job. CPU synthesis is slow, so revocation reliably lands mid-job, and killing the subprocess is visible within seconds.
- **Fallback, agreed in advance:** if spike M6 shows IndicF5 can't run on the demo laptop, the demo instead revokes during a **Kaggle-dispatched** job and shows the import being refused and the remote copies being deleted. It also **runs the deterministic checkpoint tests on screen**.
- **Tests:**
  - a barrier test for each checkpoint (`MockSpeechSynthesisProvider`);
  - a subprocess-kill test;
  - a Kaggle-path test with a mocked CLI;
  - concurrency tests (revoke vs. save in both orders; the save-carries-old-version case);
  - a deadlock test using the lock order;
  - an expiry-sweep test;
  - a matrix of every use × consent state.

## Consequences

- **+** Locally, revocation stops synthesis within seconds. The lock is on a stable row, so the race argument holds.
- **+** By default no source audio leaves the laptop. External ASR needs explicit consent.
- **−** Kaggle runs can't be cancelled. The guarantee there is "nothing produced after revocation is accepted, and remote copies are deleted". It must be described exactly like this.
- **−** A missing checkpoint is a bypass. Mitigated by the required `ConsentCheck` parameter and one test per checkpoint.
- **Viva in 2 minutes:** "One function decides consent at every stage boundary. Revocation and saving both lock the person's row, and a save only succeeds if the consent version it was given is still the latest and active. Local synthesis is killed within seconds. Kaggle output is refused at import and the remote copies are deleted."
