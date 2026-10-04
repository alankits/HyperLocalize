# ADR 0003: Postgres-backed job queue with explicit job states

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.5

## Context

Video processing is slow and must never block a web request (CLAUDE.md §6). Jobs must survive restarts, report clear states, retry provider errors, and be **cancellable mid-run** when consent is revoked (ADR 0006). Scene regeneration must re-run only that scene's work.

## Options Considered

| Criterion | In-process background tasks | Postgres-backed queue + worker | Celery + Redis/RabbitMQ | Workflow engine (e.g. Temporal) |
|---|---|---|---|---|
| Survives restart | No | Yes | Yes | Yes |
| Job claim + consent check in one transaction | No | Yes | No (two systems) | No |
| Extra infrastructure | None | None | Broker | Heavy |
| Throughput | Low | Moderate | High | High |
| Explainability | High | High ("a jobs table with states") | Medium | Low |

## Decision

A `Job` table in PostgreSQL, claimed by workers with `SELECT … FOR UPDATE SKIP LOCKED`. States:

```
QUEUED → RUNNING → SUCCEEDED
                 → FAILED            (attempts < max_attempts → QUEUED, with backoff)
QUEUED  → CANCELLED                  (e.g. consent revoked before start)
RUNNING → CANCEL_REQUESTED → CANCELLED   (worker stops at next checkpoint)
```

- Each pipeline stage is its own job type (transcribe, segment, translate, verify, synthesise scene, render scene, export, delete voice profile).
- Synthesis processes **one segment at a time** and checks consent and cancellation between segments (ADR 0006).
- Running jobs write a heartbeat. A job whose heartbeat has expired is returned to `QUEUED` (if retryable) or set to `FAILED`.
- `CANCELLED` with reason `CONSENT_REVOKED` is terminal and never retried.
- Every state change is audited (ADR 0007).

Whether to use an existing library or a small hand-written queue is a **minor decision**, made once the framework ADR (group B2) is approved. Candidates to verify: Procrastinate, and the Django tasks framework with a database backend. Any library must support the states, cancellation and heartbeats above, or be wrapped so that it does.

## Consequences

- **+** No broker to run. Consent checks and job claims are transactionally consistent.
- **+** Easy to inspect: job state is a table query.
- **−** Polling latency and moderate throughput. Acceptable at demo scale.
- **−** A hand-written queue needs careful tests for retries, stuck jobs and concurrent claims.
