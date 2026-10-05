# ADR 0020: Demo reset by rebuild, offline-copy register, and identity withdrawal

**Status:** **Proposed** (2026-10-06), waiting for approval. If approved, it **amends** ADR 0006 §5, ADR 0012 §7 and ADR 0014 (data model). Those three ADRs are not edited until then.
**Source:** consent review #2 (`docs/spike/CONSENT_FORM_REVIEW.md`); `docs/STATUS.md` known issues; ADRs 0006, 0007, 0012, 0014; consent form §8 and Part D (D2, D3).

## Context

ADR 0012 §7 says: "`manage.py demo_reset` restores a database and media snapshot of the prepared project before each rehearsal and the final demo." It is needed because the live revocation demo purges the reference clip, so every rehearsal uses up the demo state. Read against the other accepted ADRs and the revised consent form, this causes three problems. Problems 1 and 2 are [CONFIRMED] from the ADR text. Problem 3 is [INFERRED]: restoring a whole-database snapshot taken at time T loses every row added after T, whatever tool does the restore.

1. **Withdrawal can't reach the snapshot.** ADR 0006's purge deletes cloned audio, the VoiceProfile clip and the Kaggle copies. It doesn't know about the snapshot, the pre-rendered seed audio or the backup screen recording (ADR 0012 §3). But consent form §8 now promises that withdrawal deletes "the demo reset snapshot, the backup screen recording … and any copy in the HyperLocalize system".
2. **A restore brings a revoked speaker back.** Restoring a database snapshot puts back the old ACTIVE Consent rows, so a speaker who really withdrew would be "un-revoked" by the next rehearsal.
3. **A restore silently cuts the audit history.** ADR 0007's triggers block `UPDATE`, `DELETE` and `TRUNCATE` on `AuditRecord`, but a database restore replaces the table and bypasses them. Every audit record written after the snapshot is lost, possibly including a real withdrawal. The records that remain still form a valid chain, so the verifier can't detect the cut (ADR 0007's threat table: detection works only for records older than a chain head copied out earlier).

**Constraints:**
- zero budget; a small team with little DevOps experience (Q2);
- rehearsals must stay quick;
- the live revocation demo must still really revoke in the system;
- the demo revocation must not end the speaker's real consent (consent form D2), but a **real** withdrawal must be final.

## Options Considered

| Criterion | **A. Keep the snapshot; manual withdrawal checklist** | **B. Keep the snapshot; register it and guard the restore** | **C. Rebuild, don't restore: seeded reset, offline-copy register, owner-level withdrawal** | **D. No reset: rerun the real flow before each rehearsal** |
|---|---|---|---|---|
| Keeps the §8 promise (withdrawal deletes all copies) | Only if a person remembers | Yes, for registered copies | **Yes, in code, for registered copies** | Yes (there are no extra copies) |
| A real withdrawal can't be undone by a reset | **No**: the restore brings back ACTIVE consent | Yes, if the guard works | **Yes**: the reset refuses a withdrawn owner | Yes |
| Audit integrity (ADR 0007) | **Broken**: the restore cuts the chain silently | **Broken**: same | **Kept**: the reset only appends | Kept |
| Rehearsal reliability | High | High | High (once the seed exists) | **Low**: needs the speaker and, under Plans C/D, an overnight render for every rehearsal |
| Privacy (copies outside the purge) | Snapshot and recording unmanaged | Registered, purged | Registered, purged | None |
| Data model change | None | +1 model | +1 model, +1 field | None |
| Effort [ESTIMATE] | Very low | Low–medium | **Medium**: 1 model, 1 field, a reset command (about 1–2 days) | Low code, high rehearsal time |
| Cost | ₹0 | ₹0 | ₹0 | ₹0 |
| Scalability | Demo-only in every option | | | |
| Viva: explain in 2 minutes | Easy to explain, hard to defend | Hard to defend ("your reset deletes audit records") | **Easy**: "reset never rewrites history" | Easy, but the demo is fragile |

## Decision (proposed)

**Option C.**

**1. Reset rebuilds and never restores.** `manage.py demo_reset` **never overwrites the database or deletes rows**. Each run:
- **refuses** if any identity owner in the seed is withdrawn (§3), or if a seed file's SHA-256 doesn't match its `OfflineCopy` row;
- creates a **new** project, "Demo (reset <timestamp>)", from the **demo seed**: the script, the approved translations and the stock-voice settings as JSON, the reference clip, and any pre-rendered cloned audio (Plans B, C and D);
- grants a **new Consent version** scoped to that project, with evidence = the paper form ID and version and the Part D2 tick, and actor = the Administrator who ran the reset;
- creates the VoiceProfile through the normal gate (CP1);
- imports pre-rendered cloned audio through the normal locked save (CP5), so the consent check still applies;
- writes `CONSENT_GRANTED (reason: DEMO_RESET)` and `DEMO_RESET` audit records.

Earlier rehearsal projects stay in the database. Their cloned audio was already purged by the demo revocation. Their stock-voice and text artefacts remain, marked archived.

**2. `OfflineCopy` register** (new model, parallel to ADR 0014's `RemoteCopy`):
- **Fields:** identity_owner, kind (`DEMO_SEED_REFERENCE` / `DEMO_SEED_CLONED_AUDIO` / `SCREEN_RECORDING`), storage_key (under `media/offline/`), sha256, created_at, deleted_at, status (`PRESENT` / `DELETION_PENDING` / `DELETED`).
- Seed files are registered when the seed is built.
- The backup screen recording (ADR 0012 §3) is made outside the system, so it is registered with `manage.py register_offline_copy`.
- `check_providers` (ADR 0012 §1) **warns about any file in `media/offline/` that has no `OfflineCopy` row**.
- A screen recording that contains several speakers is linked to each of them. Withdrawal by any one of them deletes the whole recording.

**3. Identity withdrawal is separate from scope revocation.**
- **Scope revocation** (ADR 0006 §5, unchanged) applies to one project's scope, so the live demo revocation affects only that rehearsal project, not the golden project.
- **Withdrawal** is a new owner-level action by an Administrator, recorded as `IdentityOwner.withdrawn_at` and `withdrawn_by` (new fields), with an `IDENTITY_WITHDRAWN` audit record. In one transaction, under the IdentityOwner lock (ADR 0006 §4), it:
  - revokes **every** scope;
  - runs the ADR 0006 §5 cascade for each;
  - marks every `OfflineCopy` of that owner `DELETION_PENDING`.

  The purge then deletes those files with the same "deletion pending" retry and audit behaviour (ADR 0006 §5).
- `require_active_consent` also returns false when `withdrawn_at` is set. This is a second check in the same gate, not a new gate.
- Withdrawal **can't be undone** in the system. A speaker who comes back needs a new paper form and a new IdentityOwner.

**4. What stays outside the system's reach** (stated in the docs and the consent form, as now):
- copies the system never saw (USB sticks, phones, someone filming the demo);
- Kaggle's internal retention;
- audio already sent to Groq.

**5. Tests:**
- a reset never changes or removes existing `AuditRecord` rows (the chain prefix hash is the same before and after);
- a reset refuses a withdrawn owner;
- a reset refuses a seed whose hash doesn't match;
- withdrawal purges every `OfflineCopy` (including the `DELETION_PENDING` retry);
- a demo-scope revocation leaves the golden project's consent and artefacts untouched;
- after withdrawal, the gate refuses every use × scope;
- `check_providers` flags an unregistered file in `media/offline/`.

## Weaknesses and edge cases

- **The register only covers what it is told about.** A screen recording that nobody registers is invisible to the purge. Mitigations: the `check_providers` warning, a fixed folder and the demo-day checklist. It still depends on people.
- **Re-granting consent on every reset could look like consent theatre.** Answer for the viva: each grant is a new, audited version backed by the paper form's D2 tick, which authorises repeated demonstration revocations, and a real withdrawal blocks every future grant.
- **The demo seed is a second copy of the reference clip** for as long as the demo exists. This is deliberate: it is registered, hashed and purged on withdrawal, and covered by consent Part D. It is deleted at the Part D end date.
- **The database fills with rehearsal projects.** That is acceptable for a demo. An archive filter in the UI hides them.
- **This is new scope for the build:** 1 model, 2 fields, 2 commands and about 7 tests. That is justified because the alternatives break an accepted ADR (0007) or a promise in the consent form.
- **Spike phase:** there is no system yet. During the spike, withdrawal is done by hand and logged in the spike log (consent form §8). This ADR applies from the first system build.

## Consequences

- **+** The consent form §8 promise becomes something the code enforces for registered copies.
- **+** Audit history is append-only in practice, not just under the triggers, because no operation ever restores the database.
- **+** The difference between a demonstration revocation and a real withdrawal is explicit, and it is enforced in the backend.
- **−** More code than a `pg_restore` script: ADR 0014 gains `OfflineCopy` and `IdentityOwner.withdrawn_at` / `withdrawn_by`, and the UML class diagram needs these added. **UML diagrams to update: class diagram (2 changes) and the UC7 activity or sequence diagram (the withdrawal path).**
- **−** Rehearsal discipline is still needed for screen recordings.
- **Viva in 2 minutes:** "Reset never rewrites history. It builds a fresh demo project and re-grants consent from the signed form, and the audit log only grows. Revoking in the demo affects one project. A real withdrawal revokes everything, deletes every registered copy including the demo seed and the recording, and blocks any future reset for that person."
