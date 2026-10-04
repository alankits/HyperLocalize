# ADR 0003: Postgres-backed job queue with explicit job states

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.5

## Context

Video processing is slow and must never block a web request (CLAUDE.md §6). Jobs must survive restarts, report clear states, retry provider errors, and be **cancellable mid-run** when consent is revoked (ADR 0006). Scene regeneration must re-run only that scene's work. The team has little DevOps experience (Q2), and every provider is a hosted API with rate limits (Q4).

## Options Considered

| Criterion | In-process background tasks | Hand-written `Job` table + worker command | Job library on Postgres (e.g. Procrastinate, Django tasks with a DB backend) | Celery + Redis |
|---|---|---|---|---|
| Survives restart | No | Yes | Yes | Yes |
| Job claim + consent check in one transaction | No | Yes | Usually; depends on the library | No (two systems) |
| `CANCEL_REQUESTED` + checkpoint cancellation | No | Exactly as designed | Must be added on top | Must be added on top |
| Extra infrastructure | None | None | None | Broker |
| Learning curve for this team | Low | Low (one model + one loop) | Medium (library concepts and configuration) | High |
| Explainability in a viva | High | **High: every line is ours** | Medium | Medium |

## Decision

A **hand-written** `Job` model in the `pipeline` app, plus a Django management command, `python manage.py run_worker`. **No job library.** The review found that any library would still need our own cancellation and consent checkpoints, so it adds concepts without removing work.

States:

```
QUEUED → RUNNING → SUCCEEDED
                 → FAILED              (attempts < max_attempts → QUEUED after a back-off delay)
QUEUED  → CANCELLED                    (e.g. consent revoked before the job started)
RUNNING → CANCEL_REQUESTED → CANCELLED (worker stops at its next checkpoint)
```

- **Claiming** a job uses `select_for_update(skip_locked=True)` on the oldest QUEUED job whose `run_after` time has passed.
- **One worker process** in the MVP. The design still allows more workers later.
- **Heartbeat:** a RUNNING job updates `heartbeat_at` at every checkpoint. On startup, and every minute after that, the worker returns jobs whose heartbeat is older than a timeout (default 5 minutes [PROPOSED]) to QUEUED if they are retryable, or marks them FAILED.
- **Job types:** `transcribe`, `segment`, `translate`, `verify`, `synthesise_scene`, `render_scene`, `build_export`, `delete_voice_profile`. Regeneration re-queues only the jobs for that scene.
- Synthesis processes **one segment at a time** and checks consent and cancellation between segments (ADR 0006).
- **Provider rate limits** (e.g. free-tier requests-per-minute limits) are handled by the provider adapter. It waits and retries with a back-off and does not fail the job (ADR 0005).
- **Retries** are only for transient errors: timeouts, rate limits and 5xx responses. Validation errors and `CONSENT_REVOKED` are terminal.
- **Idempotent stages:** each job writes new versioned rows, so a retried job never overwrites or duplicates committed output.
- **Progress in the UI:** the page polls job status every 2 seconds (ADR 0010) and shows the current state, segment progress and the last error message.
- Every state change is audited (ADR 0007).

## Consequences

- **+** No broker and no library to learn; the whole queue is one model and one loop that a student can explain.
- **+** Cancellation and consent checkpoints fit naturally.
- **−** The team owns the correctness of retries and stale-job recovery. This needs explicit tests: concurrent claim, crash recovery, retry limit, and cancellation in each state.
- **−** Polling and moderate throughput. Acceptable at demo scale.
- **Viva in 2 minutes:** "Jobs are rows with a state. The worker takes the next row with `SKIP LOCKED`, checks consent, and records each step. Revocation flips a flag the worker checks between segments."
