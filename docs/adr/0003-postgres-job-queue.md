# ADR 0003: Postgres-backed job queue with explicit job states

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-04; revised 2026-10-05: ADR review, zero-budget runtimes, independent review.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.5

## Context

Video processing is slow and must never block a web request (CLAUDE.md §6). Jobs must survive restarts, report clear states, retry provider errors, and be **cancellable mid-run** when consent is revoked (ADR 0006). Scene regeneration must re-run only that scene's work. The team has little DevOps experience (Q2). Q4 allows only free tiers, local open-source models on a CPU-only laptop, and Kaggle GPU batch runs. **A local CPU synthesis job can run for many minutes**, so it must not block other work.

## Options Considered

| Criterion | In-process background tasks | Hand-written `Job` table + worker command | Job library on Postgres (e.g. Procrastinate, Django tasks with a DB backend) | Celery + Redis |
|---|---|---|---|---|
| Survives restart | No | Yes | Yes | Yes |
| Job claim + consent check in one transaction | No | Yes | Usually; depends on the library | No (two systems) |
| Cancellation at our checkpoints | No | Exactly as designed | Must be added on top | Must be added on top |
| Extra infrastructure | None | None | None | Broker |
| Learning curve for this team | Low | Low (one model + one loop) | Medium | High |
| Explainability in a viva | High | **High: every line is ours** | Medium | Medium |

## Decision

A **hand-written** `Job` model in the `pipeline` app, plus a Django management command, `python manage.py run_worker --lane <lane>`. **No job library**, because any library would still need our own cancellation and consent checkpoints.

**States** (`cancel_requested` is a **flag**, not a state; *the two reviews disagreed on this, and the flag was chosen because it's simpler*):

```
QUEUED ──claim──▶ RUNNING ──▶ SUCCEEDED
   │                 │──▶ FAILED            (attempts < max_attempts → QUEUED after back-off)
   │                 │──▶ CANCELLED         (cancel_requested seen at a checkpoint, or subprocess killed)
   │                 └──▶ DISPATCHED        (remote Kaggle batch submitted; worker released)
   └──▶ CANCELLED                           (cancelled before it was claimed)

DISPATCHED ──poll: complete──▶ RUNNING      (the import step is claimed by the next free worker in the same lane)
DISPATCHED ──cancel_requested──▶ CANCELLED  (stop polling; delete remote kernel and dataset)
DISPATCHED ──dispatch timeout──▶ FAILED     (Kaggle 12-hour session limit + margin; remote copies deleted)
```

**Two worker lanes** *(added after independent review: one worker would let a long CPU synthesis block everything else during a demo)*:

| Lane | Job types |
|---|---|
| `synthesis` | `synthesise_scene` (local CPU), `synthesise_project_remote` (Kaggle dispatch and import, batched per project, ADR 0019) |
| `default` | `transcribe`, `segment`, `translate`, `verify`, `render_scene`, `build_export`, `purge_identity_data`, `consent_expiry_sweep` |

The two lanes are two processes and two Compose services running the same code. Each claims with `select_for_update(skip_locked=True)` filtered by its job types.

**Heartbeat.** RUNNING jobs update `heartbeat_at` from the **1-second wait loop**, not only at checkpoints. That way a single slow CPU segment can't trip the stale-job timeout (default 5 minutes [PROPOSED]). Stale RUNNING jobs go back to QUEUED (if retryable) or to FAILED. DISPATCHED jobs use the dispatch timeout instead.

**Local models** run in an **inference subprocess** owned by the worker, with one model loaded at a time (ADR 0005). The worker polls `cancel_requested` and consent about once a second while waiting, and kills the subprocess on cancel.

**Remote batch jobs** release the worker while DISPATCHED. The poll (every 60 s [PROPOSED]) checks `kaggle kernels status`, then imports outputs through the locked save checkpoint (ADR 0006).

**Lock order** *(added after independent review, to prevent deadlocks)*, used by every transaction that takes more than one lock:
1. `IdentityOwner`
2. `Job`
3. artefact rows
4. `AuditChainHead`, **always last**

A concurrency test runs revocation, saves and audit writes in parallel.

**Other rules:**
- Retries only for transient errors (timeouts, rate limits, 5xx). Validation errors and `CONSENT_REVOKED` are terminal.
- Idempotent stages: new versioned rows, never overwrites.
- The UI polls job status every 2 seconds (ADR 0010).
- Job **state changes** are audited. Heartbeats and polls are not.

## Consequences

- **+** No broker and no library; the whole queue is one model, one loop and two lanes.
- **+** A long CPU synthesis can't block stock-voice regeneration or Kaggle imports.
- **−** The team owns retry, heartbeat and crash-recovery correctness. This needs explicit tests: concurrent claim, crash recovery, retry limit, cancellation in each state, dispatch timeout.
- **Viva in 2 minutes:** "Jobs are rows with a state. Two worker processes take rows with `SKIP LOCKED`: one for slow synthesis, one for everything else. Cancellation is a flag the worker checks every second; for local synthesis it kills the model process."
