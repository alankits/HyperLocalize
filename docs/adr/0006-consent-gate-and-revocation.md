# ADR 0006: Consent gate, checks at each stage boundary, revocation cascade

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §3.4, §6.8; CLAUDE.md §5

## Context

Consent must be enforced in the backend before any operation that uses a Speaker / Identity Owner's identity. Revocation must actually stop things, including **jobs that are already running** (CLAUDE.md §5). A single check when a job is claimed is not enough: a Tamil synthesis job makes one hosted API call per segment and can run for minutes (free-tier rate limits make it slower still), so a revocation during the job would otherwise be ignored until it finished. The live revocation demo must work **mid-job**.

Q6 (answered): external APIs may receive voice data, and the demo uses only team members' voices. Any real third-party content would need its own consent records. Faces are not processed (Q5). Whether cloned voice is viable in Tamil is pending the spike (ADR 0015). This ADR applies to any approved identity use.

## Options Considered

| Criterion | UI-only checks | Check once at job claim | Gate at every stage boundary + locked check-and-save | Signed capability tokens per job |
|---|---|---|---|---|
| Meets CLAUDE.md §5 | No | No | Yes | Yes |
| Stops a running job | No | No | Yes, at the next checkpoint | Only with revocable tokens, which means a DB check again |
| Race between revoke and save | — | Present | Closed by row locks | Needs the same locking |
| Explainability | — | High | High | Medium |

## Decision

**1. One gate.** `require_active_consent(identity_owner, use, project, language)` in the `identity` app is the only code that decides whether identity may be used. It also checks the job's `cancel_requested` flag. It returns a `ConsentCheck` (consent id + version), which identity-using provider methods require (ADR 0005).

**2. What counts as identity use.** Creating a voice profile, synthesis in `CLONED_VOICE` mode, rendering or mixing a scene with cloned audio, approving a snapshot containing it, exporting it, and serving it. `STOCK_VOICE` and `SUBTITLES_ONLY` do not use identity.

**3. Checkpoints, one at every stage boundary.**

| # | Stage boundary | On failure |
|---|---|---|
| CP1 | API request that would use identity | Refuse; audit `CONSENT_DENIED` |
| CP2 | Job claim (same transaction) | `CANCELLED` |
| CP3 | Before voice-profile enrolment (before audio leaves the system) | `CANCELLED`; nothing sent |
| CP4 | **Before synthesis, for each segment** | Stop; `CANCELLED` |
| CP5 | Saving synthesised audio (locked) | Discard; delete temp files |
| CP6 | **Before scene render / mix** | `CANCELLED` |
| CP7 | Saving the rendered scene (locked) | Discard |
| CP8 | Approval (every consent version in the snapshot still active) | Refuse approval |
| CP9 | **Before export build, and when saving the export (locked)** | `CANCELLED` |
| CP10 | Serving previews and export downloads | `410 Gone`, with an explanation |

**4. Race-free saving: both sides take the same lock.** *(Changed in the review: the earlier `FOR SHARE` design is not available through Django's ORM. Using `FOR UPDATE` on both sides is simpler to explain and still correct.)*
- Revocation runs `select_for_update()` on the Consent row.
- Each save checkpoint (CP5, CP7, CP9) also runs `select_for_update()` on the same Consent row, re-checks that it is ACTIVE, and inserts the artefact with its `consent_id` and `consent_version`, all in one transaction.
- The two transactions therefore take turns. Either the artefact is saved first and the revocation that follows finds and quarantines it, or the revocation goes first and the save sees REVOKED and aborts. Neither order leaves an active artefact under revoked consent.
- Cost: saves for the same speaker also take turns among themselves. With one worker (ADR 0003), that cost is zero.

**5. Revocation transaction.** Write a new REVOKED consent version. Then:
- cancel QUEUED jobs that use it;
- set `cancel_requested` on RUNNING ones;
- quarantine every artefact recorded under it;
- invalidate approvals whose snapshot includes it;
- mark affected exports `CONSENT_REVOKED`;
- queue a `delete_voice_profile` job;
- write the audit record.

**6. Revoked during a running job (defined behaviour).**
1. The job stops at its next checkpoint. Per-segment synthesis keeps the delay to about one provider call plus one save.
2. A provider call already in flight is not interrupted; its result is discarded and temp files are deleted.
3. The job ends `CANCELLED` with reason `CONSENT_REVOKED`, and is never retried.
4. Segments saved earlier in that job are quarantined by the cascade.
5. The scene becomes `NEEDS_REGENERATION`, and a fallback render (`STOCK_VOICE` / `SUBTITLES_ONLY` per policy) is queued that **requires review again**.
6. The Localization Manager sees a notice on the project page.
7. The provider-side voice is deleted by the `delete_voice_profile` job. If deletion fails, it is retried and shown as **"deletion pending"** to the Administrator. It is never shown as done until the provider confirms it.

**7. Exports already downloaded cannot be recalled.** This is stated in the UI and the docs. The system blocks further downloads and marks the export revoked.

**8. Consent evidence.** Each Consent version stores who granted it, when, the scope (uses, project, languages, expiry), the named processors (provider names), and an evidence file. For the demo the evidence file is the signed consent form. Optionally the speaker also records a short spoken consent statement.

**9. Demo safety.**
- The revocation demo uses a scene with enough segments that revocation always lands mid-job; at provider speed, that is roughly 30 seconds or more of synthesis (to be confirmed by spike M5).
- A **deterministic integration test** covers every checkpoint, using a barrier in `MockSpeechSynthesisProvider` (pause, revoke, release, assert).
- A **concurrency test** covers revoke vs. save in both orders.
- A **test matrix** covers every identity operation × consent state {none, active, expired, revoked, wrong use, wrong project, wrong language}.

## Consequences

- **+** Revocation provably reaches running jobs at defined points, and the demo doesn't depend on lucky timing.
- **+** Every artefact carries the consent version it was made under, which feeds the evidence manifest.
- **−** A missing checkpoint is a bypass. Mitigated by the required `ConsentCheck` parameter and one test per checkpoint.
- **−** The time to stop is bounded by the longest single provider call. It is a **measured** value (spike M5), not a guarantee.
- **−** Provider-side deletion depends on the provider's own behaviour. We can show that the delete API call succeeded; we cannot prove what the provider kept.
- Retention for quarantined media: deleted after 7 days [PROPOSED default; to be confirmed].
- **Viva in 2 minutes:** "One function decides consent, and it runs at every stage boundary. Revocation and saving take the same lock, so they can't interleave. A running job stops at the next segment, and its output is quarantined and replaced by a stock-voice fallback that needs review again."
