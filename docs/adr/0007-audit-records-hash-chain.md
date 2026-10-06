# ADR 0007: Append-only, hash-chained audit records

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-04; revised 2026-10-05: ADR review, independent review. **Amended 2026-10-06 by ADR 0020** (new audited actions).
**Source:** `docs/PHASE0_DISCOVERY.md` §6.10; CLAUDE.md §5

## Context

Every consent grant and revocation, approval, regeneration and export must produce an audit record (who, what, when, which project or scene, which consent version). Use case 9 (Inspect Quality, Audit and Evidence) requires auditors to inspect this history, and exports should carry evidence. The design must not overclaim its security properties. The team has little DevOps experience (Q2), so the hardening must not depend on complex database administration.

## Options Considered

| Criterion | Application log lines | Append-only table, same transaction as the action | Append-only table + SHA-256 hash chain | External ledger or blockchain |
|---|---|---|---|---|
| Completeness | None | High | High | High |
| Detects edits | No | No | Some (see threat model) | Yes, against the ledger |
| Complexity | Low | Low | Low–medium | High; not justified |

## Decision

**Record.** An `AuditRecord` table in the `audit` app: `seq`, actor, action, entity type and id, project, scene, consent version, timestamp (UTC), details (JSON; **identifiers and hashes only, never raw transcripts or audio**), `prev_hash`, `hash`.

**Canonical hashing** *(added in the review; without it, verification would fail on formatting differences):*
- `hash = SHA-256(prev_hash + canonical_json(record))`.
- `canonical_json` means sorted keys, UTF-8, no whitespace, timestamps as ISO-8601 UTC strings with microseconds, and no floats (decimals as strings).

**Writing.**
- Records are written only through `audit.services.record(...)`, **inside the same transaction** as the action they describe. *(amended by ADR 0020, 2026-10-06)* Exception: `DEMO_RESET_REFUSED` records a refusal, so there is no action transaction to share; it is written in its own transaction.
- Appends are serialised by `select_for_update()` on a single `AuditChainHead` row, so the chain stays linear. **`AuditChainHead` is always locked last** (the global lock order is in ADR 0003), which prevents deadlocks with consent and job locks.
- **What is audited:** consent grants, revocations and expiries; approvals and invalidations; regeneration requests; exports; check overrides and acknowledgements; provider-chain and policy changes; provider fallbacks and Gemini skips; job state changes. *(amended by ADR 0020, 2026-10-06)* Also: `SEED_BUILT`, `DEMO_RESET`, `DEMO_RESET_REFUSED`, `OFFLINE_COPY_REGISTERED`, `OFFLINE_COPY_DELETED` and `IDENTITY_WITHDRAWN`. `CONSENT_GRANTED` gains the reason `DEMO_RESET` and `parent_consent_id`; `CONSENT_REVOKED` gains `removed_uses` (narrowing) and the reason `EXPIRED`. One action may write more than one record (for example a withdrawal: `IDENTITY_WITHDRAWN` plus one `CONSENT_REVOKED` per scope), all in the same transaction. **Not audited:** heartbeats and status polls (they would bury the evidence).

**Append-only.** PostgreSQL triggers, created in a Django migration, reject `UPDATE` and `DELETE` (row-level) and **`TRUNCATE`** (statement-level; added after review) on the table. *(Changed in the review: a separate restricted database role is now **optional hardening**, not part of the MVP, because it adds database administration the team hasn't done before. The threat model below reflects this.)*

**Verification.** `python manage.py verify_audit_chain` recomputes the chain and reports the first mismatch. The Auditor screen (UC9) shows the last verification result and time, and **filters records by action type and project**, so the demo isn't buried in job events.

**Chain head in every export.**
- Inside the export transaction, the evidence manifest records the latest chain head (`seq`, `hash`, `timestamp`).
- The `EXPORT_CREATED` audit record that follows stores the manifest's SHA-256.
- Every export that leaves the system therefore carries a copy of the head, and later the verifier can show the history up to that point is unchanged.

### Threat model

The hash chain is **tamper-evident, not tamper-resistant**, against anyone with database access. It can reveal some kinds of tampering. It cannot prevent any of them.

| Threat | Prevented? | Detected? |
|---|---|---|
| App user modifies records through the UI or API | Yes (no such endpoint exists) | — |
| Application bug skips a record | No | By audit-completeness tests, not by the chain |
| Someone with DB access runs `UPDATE`/`DELETE` while the trigger is active | Blocked by the trigger, but anyone who owns the table can disable the trigger | — |
| DB-level edit or delete (trigger disabled) without recomputing later hashes | No | Yes, by the verifier |
| DB-level edit **with** a full chain recompute | No | Only for records older than a chain head copied out earlier (e.g. inside an export). Otherwise no. |
| Forged records appended by anyone who can insert | No | No (the hash uses no secret key) |
| Tail truncation or backup rollback | No | Only against a later chain head held outside the database |
| Root access to the server | No | No guarantee |

Possible future strengthening, each needing its own ADR and none part of this decision:
- a restricted database role for the app;
- keyed hashes (HMAC, with the key outside the database);
- publishing the chain head externally at intervals;
- digital signatures.

## Consequences

- **+** Complete, transactional history; naive tampering is detected; every export carries a checkable link to the history.
- **−** It does not resist tampering. The docs, UI and viva must describe it exactly as in the threat model.
- **−** Serialised appends limit throughput. Acceptable at demo scale.
- **Viva in 2 minutes:** "Each audit record includes the hash of the one before it, so editing an old record breaks the chain and the verifier finds it. Someone with database access could rebuild the whole chain, which is why every export carries a copy of the latest hash. We call this tamper-evident, and we don't claim more."
