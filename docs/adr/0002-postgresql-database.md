# ADR 0002: PostgreSQL as the primary database

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.4

## Context

The core entities are strongly relational (Consent → Job → RenderedScene → Approval → Export → AuditRecord). Consent enforcement relies on row locking to serialise revocation against output persistence (ADR 0006). The job queue should live in the same database so that claiming a job and checking consent happen in one transaction (ADR 0003). Provider outputs and manifests are semi-structured.

## Options Considered

| Criterion | PostgreSQL | SQLite | MongoDB |
|---|---|---|---|
| Relational integrity, foreign keys | Yes | Yes | Weak |
| Row locks (`FOR UPDATE`, `FOR SHARE`, `SKIP LOCKED`) | Yes | No (one writer at a time for the whole database) | Different model |
| Concurrent API + worker writes | Yes | Limited | Yes |
| JSON for semi-structured data | JSONB | JSON functions | Native |
| Operations | Needs a server (one container) | None | Needs a server |

## Decision

Use PostgreSQL for all application data, the job queue, and audit records. **Tests run against PostgreSQL, not SQLite**, so locking, constraint and trigger behaviour is actually exercised.

## Consequences

- **+** Locking semantics support ADR 0003 and ADR 0006 directly.
- **+** Triggers and role privileges support the append-only audit table (ADR 0007).
- **−** Developers and CI need a running Postgres (Docker).
- **−** The team must understand basic locking and isolation (`READ COMMITTED`) well enough to explain ADR 0006 in a viva.
- Encryption at rest and backups are [UNKNOWN] and must not be claimed until configured and documented.
