# Architecture Decision Records

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith with a separate worker process | Proposed |
| [0002](0002-postgresql-database.md) | PostgreSQL as the primary database | Proposed |
| [0003](0003-postgres-job-queue.md) | Postgres-backed job queue with explicit job states | Proposed |
| [0004](0004-media-storage-interface.md) | Media storage behind an interface, local filesystem for the MVP | Proposed |
| [0005](0005-provider-abstraction-and-mocks.md) | AI provider abstraction with clearly named mock providers | Proposed |
| [0006](0006-consent-gate-and-revocation.md) | Consent gate, checks at each stage boundary, revocation cascade | Proposed |
| [0007](0007-audit-records-hash-chain.md) | Append-only, hash-chained audit records | Proposed |
| [0008](0008-critical-information-verification.md) | Critical-information verification: rule-based hard checks + AI flags | Proposed |

Pending ADRs (not yet written): see `docs/PHASE0_DISCOVERY.md` §12.
- Group B1 is decided after the spike: identity feasibility, translation method, ASR provider, TTS / voice provider.
- Group B2 is decided by open answers: framework, frontend, auth, hosting, data model.
