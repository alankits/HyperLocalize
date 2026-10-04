# ADR 0007: Append-only, hash-chained audit records

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.10; CLAUDE.md §5

## Context

Every consent grant and revocation, approval, regeneration and export must produce an audit record (who, what, when, which project or scene, which consent version). Use case 9 (Inspect Quality, Audit and Evidence) requires auditors to inspect this history, and exports should carry evidence. The design must not overclaim its security properties.

## Options Considered

| Criterion | Application log lines | Append-only table, same transaction as the action | Append-only table + SHA-256 hash chain | External ledger or blockchain |
|---|---|---|---|---|
| Completeness | None | High | High | High |
| Detects edits | No | No | Some (see threat model) | Yes, against the ledger |
| Complexity | Low | Low | Low–medium | High; not justified |

## Decision

- An `AuditRecord` table: `seq`, actor, action, entity type and id, project, scene, consent version, timestamp, details (JSON; **identifiers and hashes only, never raw transcripts or audio**), `prev_hash`, `hash` = SHA-256(canonical record ‖ `prev_hash`).
- Each record is written **in the same transaction** as the action it describes, only through the `audit` module.
- The application's database role has `INSERT` and `SELECT` only. A trigger rejects `UPDATE` and `DELETE`.
- Appends are serialised by locking the chain head, so the chain stays linear.
- A verifier recomputes the chain and reports the first mismatch.
- **Every export's evidence manifest includes the latest chain head** (`seq`, `hash`, `timestamp`) at export time. The following `EXPORT_CREATED` record stores the manifest's SHA-256.

### Threat model

The hash chain is **tamper-evident, not tamper-resistant**, against anyone with database access.

| Threat | Prevented? | Detected? |
|---|---|---|
| App user modifies records through the UI or API | Yes (no endpoint; no DB privilege) | — |
| Application bug skips a record | No | By audit-completeness tests, not by the chain |
| DB-level edit or delete without recomputing later hashes | No | Yes (verifier) |
| DB-level edit **with** a full chain recompute | No | Only for records before a chain head copied out earlier (e.g. in an export). Otherwise no. |
| Forged records appended by anyone with INSERT | No | No (unkeyed hash) |
| Tail truncation or backup rollback | No | Only against a later chain head held outside the database |
| Root access to the server | No | No guarantee |

Possible future strengthening, each needing its own ADR: keyed hashes (HMAC, key outside the database), periodic external anchoring of the chain head, digital signatures. None of these is part of this decision.

## Consequences

- **+** Complete, transactional history, with detection of naive tampering and a checkable link to every export.
- **−** Not tamper-resistant. The viva and docs must describe it exactly as in the threat model above.
- **−** Serialised appends limit throughput. Acceptable at demo scale.
