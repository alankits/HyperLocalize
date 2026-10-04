# ADR 0006: Consent gate, checks at each stage boundary, revocation cascade

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §3.4, §6.8; CLAUDE.md §5

## Context

Consent must be enforced in the backend before any operation that uses a Speaker / Identity Owner's identity. Revocation must actually stop things, including **jobs that are already running** (CLAUDE.md §5). A check only at job claim is not enough: a synthesis job can run for minutes, and a revocation during it would otherwise be ignored until it finished. The live revocation demo must work mid-job.

What identity technically means (cloned voice or not) is still pending the spike (group B1). This ADR applies to whatever identity use is approved. Faces are not processed.

## Options Considered

| Criterion | UI-only checks | Check once at job claim | Gate at every stage boundary + locked check-and-persist | Signed capability tokens per job |
|---|---|---|---|---|
| Meets CLAUDE.md §5 | No | No | Yes | Yes |
| Stops a running job | No | No | Yes, at the next checkpoint | Only with revocable tokens, which means a DB check again |
| Race between revoke and persist | — | Present | Closed by row locks | Needs the same locking |
| Explainability | — | High | High | Medium |

## Decision

**1. One gate.** `require_active_consent(identity_owner, use, project, language)` in the `identity` module is the only code that decides whether identity may be used. It also checks the job's `cancel_requested` flag. It returns a `ConsentCheck` object (consent id + version), which identity-using provider methods require (ADR 0005).

**2. What counts as identity use.** Creating a voice profile, synthesis in `CLONED_VOICE` mode, rendering or mixing a scene with cloned audio, approving a snapshot containing it, exporting it, and serving it. `STOCK_VOICE` and `SUBTITLES_ONLY` do not use identity.

**3. Checkpoints.**

| # | Stage boundary | On failure |
|---|---|---|
| CP1 | API request that would use identity | Refuse; audit `CONSENT_DENIED` |
| CP2 | Job claim (same transaction) | `CANCELLED` |
| CP3 | Before voice-profile enrolment (before audio leaves the system) | `CANCELLED`; nothing sent |
| CP4 | **Before synthesis, for each segment** | Stop; `CANCELLED` |
| CP5 | Persist synthesised audio (locked) | Discard; delete temp files |
| CP6 | **Before scene render / mix** | `CANCELLED` |
| CP7 | Persist rendered scene (locked) | Discard |
| CP8 | Approval (all consent versions in the snapshot active) | Refuse approval |
| CP9 | **Before export build, and when persisting the export (locked)** | `CANCELLED` |
| CP10 | Serving previews and export downloads | `410 Gone` |

**4. Race-free persistence.** Revocation locks the Consent row `FOR UPDATE`. Each persist checkpoint (CP5, CP7, CP9) locks it `FOR SHARE`, re-checks it is ACTIVE, and inserts the artefact (recording `consent_id` and `consent_version`) in the same transaction. Because the locks conflict, either the artefact commits first and the revocation cascade (which runs after it) quarantines it, or the revocation commits first and the persist aborts.

**5. Revocation transaction.** Write a new REVOKED consent version. Then:
- cancel QUEUED jobs that use it;
- set `cancel_requested` on RUNNING ones;
- quarantine every artefact recorded under it;
- invalidate approvals whose snapshot includes it;
- mark affected exports `CONSENT_REVOKED`;
- queue a provider-side voice deletion job;
- write the audit record.

**6. Running jobs on revocation.**
- The job stops at its next checkpoint. Per-segment synthesis keeps the delay to about one provider call.
- A provider call already in flight is not interrupted; its result is discarded.
- The job ends `CANCELLED` with reason `CONSENT_REVOKED`, and is never retried.
- Earlier segments from that job are quarantined.
- The scene becomes `NEEDS_REGENERATION`, and a fallback render (`STOCK_VOICE` / `SUBTITLES_ONLY` per policy) is queued that **requires review again**.
- The Localization Manager is notified.

**7. Exports already downloaded cannot be recalled.** This is stated in the UI and the docs. The system blocks further downloads and marks the export revoked.

**8. Testing.**
- A deterministic integration test for each checkpoint, using a barrier in `MockSpeechSynthesisProvider` (pause, revoke, release, assert).
- A concurrency test of revoke vs. persist under both orderings.
- A test matrix of every identity operation × consent state {none, active, expired, revoked, wrong use, wrong project, wrong language}.

## Consequences

- **+** Revocation provably reaches running jobs at defined points, and the demo doesn't rely on timing luck.
- **+** Every artefact carries the consent version it was made under, which feeds the evidence manifest.
- **−** A missing checkpoint is a bypass. Mitigated by the `ConsentCheck` parameter requirement and the per-checkpoint tests.
- **−** Stop latency is bounded by the longest single provider call. It is a **measured** value, not a guarantee.
- **−** Provider-side deletion depends on the provider. Providers without a deletion API are excluded (ADR 0005), and deletion failures are retried and shown to the Administrator.
- **−** Shared locks add contention on hot Consent rows. Negligible at demo scale.
- Retention periods for quarantined media are [UNKNOWN] (Q15).
