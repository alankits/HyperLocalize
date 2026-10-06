# Independent code reviews of the MVP build

## Review 1: consent, identity and audit code (2026-10-06)

**Reviewer:** `critical-reviewer` agent (fresh context, read-only), on commit `4faef41`. **Verdict:** approve with changes, with 1 blocker, 6 major and 5 minor findings, plus test gaps. **Status: all fixed.** Each fix has a regression test in `hyperlocalize/tests/test_review_fixes.py`, except #9, #10 and #11, which are covered by the existing suite.

| # | Sev | Finding | Fix |
|---|---|---|---|
| 1 | Blocker | Re-granting a narrower standing or project consent bypassed the single narrowing path: no cascade, no purge, no audit | Grants refuse any narrowing and point to Narrow / Revoke |
| 2 | Major | A later cascade could cancel a queued purge job | The cascade cancels only render jobs, never the purge |
| 3 | Major | Which reference clips to delete was decided at purge time, so revoke-then-regrant kept the old clip | Profiles are marked DELETED inside the revocation transaction; the purge only deletes files |
| 4 | Major | Harmless narrowings (an earlier expiry) broke previews, approval and export, and cancelled jobs | CP5–CP10 require the owner's latest consent to pass the gate (plus the job's cancel flag); the cascade runs only when identity use ends; a cancelled regeneration returns to CHANGES_REQUESTED |
| 5 | Major | The code did not follow the declared lock order (deadlock risk) | One order everywhere: IdentityOwner → Localization → Scene → Job → artefacts → Export → AuditChainHead; fallback renders are queued after commit |
| 6 | Major | `demo_reset` linked every speaker to the one owner | Only that owner's own speaker keeps the link |
| 7 | Major | One owner's revocation invalidated and purged exports that did not contain their voice | Approvals and exports are touched only if they contain that owner's consent or an affected scene |
| 8 | Minor | The expiry sweep could expire a renewed grant | Re-checked under the lock |
| 9 | Minor | The purge had no per-item status or retry | Items are marked only after the delete; failures stay pending and the job retries; a cancelled render queues a purge |
| 10 | Minor | A gate refusal inside `demo_reset` was neither audited nor turned into a refusal | Caught and recorded as DEMO_RESET_REFUSED |
| 11 | Minor | Owner names went into the append-only log | Identifiers only |
| 12 | Tests | Some tests would pass with the property broken | Drained purges, a two-owner mid-job test, withdraw-vs-reset in both orders, scoped-export and regrant tests |
| — | Honesty | CP10 returned 404, but ADR 0006 says 410 | Now 410 Gone |
| — | Honesty | `external_transcription` is not checked by any gate | Recorded in STATUS: unenforced, because no external ASR provider exists |
