# ADR 0020: Demo reset by rebuild, offline-copy register, and identity withdrawal

**Status:** **Accepted** (2026-10-06). Accepted under the user's rule of 2026-10-06: "mark ADR 0020 accepted only if the final review has no blockers". The final consistency review found one blocker (B1), which revision 6 fixed. The re-check found one bookkeeping blocker (ADR 0006 §9 not in the Amends list), which was fixed. The narrow diff check returned **BLOCKERS: none** (`0020-REVIEW.md` round 5). **Designed, not implemented.**

**History:**
- **Revision 2** (2026-10-06): applied all 14 round-1 review findings.
- **Revision 3** (2026-10-06): applied the round-2 findings N1–N7 and the reviewer's simplification (no cloned voice in the golden project, no `DB_BACKUP` kind, one narrowing path), with the user's approval.
- **Revision 4** (2026-10-06): applied round-3 findings M1–M6, with M4 option (a): the golden project is built once by hand through the real flow and never reset. The fixes were approved by the user.
- **Revision 5** (2026-10-06): product-framing fix MF2 (`docs/PRODUCT.md`). The standing consent is now a **product-level** owner consent with generic fields (`permitted_purposes[]`, `permitted_copy_kinds[]`, uses, languages, processors, expiry). The spike consent form's Part D ticks (D1–D4) are only **mapped** onto it (§1, table), instead of being stored as product consent values. The behaviour for the spike speakers is **intended** to be unchanged; review round 4 found one accidental change (the gate for rehearsal projects) and it is fixed. See `0020-REVIEW.md` round 4. Also: N8 (the revocation-demo note, §10) is added to the history, and the Amends list is completed.
- **Revision 6** (2026-10-06): final-consistency-review fixes: blocker B1 (rehearsal consents never inherit Kaggle use, so the form's D4 "during development" limit holds) and non-blocking items 1–6, plus the re-check items (ADR 0006 §9 in Amends; remote voice processors defined; D4 removal effect; `SEED_BUILD_REFUSED`). No consent form change.
- *Note:* ADR 0020 was briefly marked Accepted on 2026-10-06 (commits `6c917e6`, `2e7538c`) and was **reverted to Proposed** the same day at the user's request. The amendments to other ADRs were rolled back.


Reviews: `docs/adr/0020-REVIEW.md`.

**Amends** (each amended ADR carries a precedence note pointing here; where they differ, **this ADR takes precedence**):
- ADR 0003: lock order among several rows of the same type (ascending id);
- ADR 0006: §1 (the gate), §4 (locked saves call the full gate), §5 (cascade scope, purge, expiry sweep, and a narrowing-and-withdrawal paragraph), §8 (standing consent as parent), §9 (in rehearsal projects the demo fallback becomes the checkpoint tests only; no Kaggle-dispatched fallback);
- ADR 0007: the list of audited actions, and the own-transaction exception for `DEMO_RESET_REFUSED`;
- ADR 0011: the Administrator and Identity Owner rows, and the viva line;
- ADR 0012: demo-resilience items 1 (`check_providers`), 2 (golden project: stock voice only, built once through the real flow), 3 (screen recording) and 7 (demo reset), plus the revocation-demo note (§10 here);
- ADR 0014: Project, Consent, IdentityOwner, Export, the new `OfflineCopy` model, invariants 1, 2 and 6, and a new invariant 8.

**Source:** consent review #2 (`docs/spike/CONSENT_FORM_REVIEW.md`); `docs/STATUS.md` known issues; ADRs 0006, 0007, 0011, 0012, 0014; consent form §6, §8 and Part D.

## Context

ADR 0012 item 7 says: "`manage.py demo_reset` restores a database and media snapshot of the prepared project before each rehearsal and the final demo." It is needed because the live revocation demo purges the reference clip, so every rehearsal uses up the demo state. Read against the other accepted ADRs and the revised consent form, this causes four problems. Problems 1, 2 and 4 are [CONFIRMED] from the ADR text. Problem 3 is [INFERRED]: restoring a whole-database snapshot taken at time T loses every row added after T, whatever tool does the restore.

1. **Withdrawal can't reach the snapshot.** ADR 0006's purge deletes cloned audio, the VoiceProfile clip and the Kaggle copies. It doesn't know about the snapshot, the pre-rendered seed audio, export package files or the backup screen recording (ADR 0012 item 3). But consent form §8 promises that withdrawal deletes "the demo reset snapshot, the golden (pre-prepared) demo project, export packages, the backup screen recording … and any copy in the HyperLocalize system".
2. **A restore brings a revoked speaker back.** Restoring a database snapshot puts back the old ACTIVE Consent rows.
3. **A restore silently cuts the audit history.** ADR 0007's triggers block `UPDATE`, `DELETE` and `TRUNCATE` on `AuditRecord`, but a database restore replaces the table and bypasses them. The records that remain still form a valid chain, so the verifier can't detect the cut (ADR 0007's threat table).
4. **ADR 0006 §5 revocation is owner-wide.** It quarantines "every `SynthesisedSegment` and `RenderedScene` recorded under that owner's consent" and purges "the VoiceProfile reference clip". So an on-stage revocation would also wipe every other project of that speaker.

**Constraints:**
- zero budget; a small team with little DevOps experience (Q2);
- rehearsals must stay quick;
- the live revocation demo must still really revoke in the system;
- a demonstration revocation must not end the speaker's real consent (consent form D2), but a **real** withdrawal (consent form Part D) must be final;
- ADR 0011: only the identity owner can grant consent, and the Administrator **cannot grant consent on anyone's behalf**.

## Options Considered

| Criterion | **A. Keep the snapshot; manual withdrawal checklist** | **B. Keep the snapshot; register it and guard the restore** | **C. Rebuild, don't restore: owner's standing grant, derived project grants, offline-copy register, one narrowing path** | **D. No reset: rerun the real flow before each rehearsal** |
|---|---|---|---|---|
| Keeps the §8 promise (withdrawal deletes all copies) | Only if a person remembers | Yes, for registered copies | **Designed to, for registered copies in the system's media folder**; the rest is on a manual checklist (§6) | Yes (there are no extra copies) |
| A real withdrawal can't be undone by a reset | **No**: the restore brings back ACTIVE consent | Yes, if the guard works | **Yes, by design**: the reset refuses a withdrawn owner or a standing consent that doesn't permit the demo purposes, under the owner's lock | Yes |
| Audit integrity (ADR 0007) | **Broken**: the restore cuts the chain silently | **Broken**: same | **Kept by the system**: the reset only appends. A manual restore remains a residual risk (§6) | Kept |
| Consistent with ADR 0011 (only the owner grants) | Depends on who restores | Same | **Yes**: the owner grants; the reset only derives narrower, project-only versions | Yes, but the owner must re-grant before every rehearsal |
| Rehearsal reliability | High | High | High (once the seed exists) | **Low**: needs the speaker and, under Plans C/D, an overnight render for every rehearsal |
| Privacy (copies outside the purge) | Snapshot and recording unmanaged | Registered, purged | Registered, purged; the golden project holds no voice | None |
| Data model change | None | +1 model | +1 model, about 8 fields | None |
| Effort [ESTIMATE] | Very low | Low–medium | **Medium**: 1 model, about 8 fields, 3 commands, 19 tests (about 2–3 days, reviewer's estimate, not measured) | Low code, high rehearsal time |
| Cost | ₹0 | ₹0 | ₹0 | ₹0 |
| Scalability | Demo-only in every option | | | |
| Viva: explain in 2 minutes | Easy to explain, hard to defend | Hard to defend ("your reset deletes audit records") | **Moderate**: "the speaker grants once; every project consent is a narrower copy; revoking in a rehearsal is the demo, revoking anywhere else is real" | Easy, but the demo is fragile |

## Decision (proposed)

**Option C.**

### 1. The owner's standing consent, and derived project grants

**Standing consent (product level).** *(Revision 5: generic fields; the spike form is only mapped onto them.)*
- The Speaker / Identity Owner signs in with their own account (ADR 0011, Q10) and grants a Consent version of a new kind, `STANDING`. It is an owner-level consent that sets the outer limits for that owner's project consents. It records:
  - `uses[]`: consent uses as defined in ADR 0006 §2 (for example `voice_synthesis`, `remote_voice_processing`);
  - `permitted_purposes[]`: which kinds of project the owner's identity may be used in, from `Project.purpose` (§2): `STANDARD` and/or `DEMO_REHEARSAL`;
  - `permitted_copy_kinds[]`: which `OfflineCopy` kinds (§4) may be kept for this owner, for example `SCREEN_RECORDING`;
  - `languages[]`;
  - `processors[]` (ADR 0006 §8);
  - `expires_at`;
  - evidence: the signed form's ID and version;
  - `granted_by`: the owner's own user.
- It has no project. **The gate never accepts it directly.** Its only role is to authorise project versions.

**How the spike consent form maps onto it** *(spike/demo mapping only; these ticks are not product consent values)*:

| Spike consent form (Part D) | Standing consent field |
|---|---|
| D1. Develop and test on the team laptop | `permitted_purposes` includes `STANDARD` |
| D2. Live demo and its team rehearsals | `permitted_purposes` includes `DEMO_REHEARSAL`, **recorded only if D1 is also ticked** (the form: "D2 needs D1"; otherwise D2 = NO) |
| D3. Backup screen recording | `permitted_copy_kinds` includes `SCREEN_RECORDING` |
| D4. Kaggle processing **during development** | `uses` includes `remote_voice_processing`, and `processors` includes Kaggle. Derived rehearsal consents never inherit these (§3), so D4 covers `STANDARD` projects only, as the form says (fixes final-review B1) |
| Any of D1–D3 ticked (with 3.1 voice synthesis) | `uses` includes `voice_synthesis` |
| The language the clone speaks (Tamil in the spike) | `languages` |
| Part D fixed end date | `expires_at` (no later than that date) |
| Form ID and version | evidence |

**Limits kept by procedure, not by the system:** the form's audience and playback limits (D1: heard by the team, R1 and R2; D3: shown only to the panel) have no system field. They are kept by the team's procedure (fixes A5).
- Changing it means a new standing version; the latest version is current (ADR 0014).
  - **Narrowing** (removing uses, permitted purposes, permitted copy kinds, languages or processors, or an earlier `expires_at`) can be done by the owner in the app alone, or by an Administrator recording a §8 request (§5).
  - **Widening** (adding anything back, or a later `expires_at`) is done only by the owner, and needs a **new signed paper form ID** as evidence (fixes M5). Without it, the system refuses the new version.

**Project consents derive from it** (fixes N3). In the MVP, every `PROJECT` Consent version must have `parent_consent` = the owner's latest standing version, and must be no wider than it:
- `uses ⊆ parent.uses`;
- `languages ⊆ parent.languages`;
- `processors ⊆ parent.processors`;
- `expires_at ≤ parent.expires_at`.

There are two ways to create one:
- **`STANDARD` project:** the owner grants it from their own account (ADR 0006 as now). The parent must permit `STANDARD`.
- **`DEMO_REHEARSAL` project:** `demo_reset` creates it with `granted_by` = system (`DEMO_RESET`), and the Administrator who ran the command is recorded as `triggered_by` in the audit details. The parent must permit both `STANDARD` and `DEMO_REHEARSAL`: for the spike speakers, that is D1 (the seed comes from a development project) and D2 (the demo and its team rehearsals).

The Administrator can trigger the copy but can't create, widen or extend consent.

**Owners without a standing consent.** In the MVP, every identity owner has a standing consent recorded from their signed form. A project consent without a parent is **refused**, and so is any use of identity for an owner with no standing consent (gate, below) [PROPOSED]. Whether the product should later let an owner grant project consent directly, without a standing consent, is [UNKNOWN]. That is a product question, not an MVP rule.

**Gate change (amends ADR 0006 §1).** `require_active_consent` also returns false if:
- `IdentityOwner.withdrawn_at` is set; or
- the owner has **no** standing version; or
- the owner's **latest** standing version is not ACTIVE, is expired, or doesn't permit what the project's purpose needs: a `STANDARD` project needs `STANDARD`; a `DEMO_REHEARSAL` project needs both `STANDARD` and `DEMO_REHEARSAL` (fixes A6; this matches revision 4, where a rehearsal needed D1 and D2); or
- the project version is **no longer within** that latest standing version: every one of its `uses`, `languages` and `processors` must still be in the standing version, and its `expires_at` must be no later (fixes M1). So narrowing a language or a processor makes the affected project scopes fail the gate, and §5 step 2 cascades them.

These are extra conditions in the same gate, not a new gate.

**Locked saves call the full gate (amends ADR 0006 §4; fixes N2).** CP5, CP7 and CP9 already lock the IdentityOwner row and re-read the latest version of their own scope. They now also run the parent and `withdrawn_at` conditions under that same lock. So a save that started before a narrowing, and commits after it, is refused.

### 2. Project purpose

A new field, `Project.purpose`, is either `STANDARD` (the default) or `DEMO_REHEARSAL`. `DEMO_REHEARSAL` is set **only** by `demo_reset`; no API or UI can set or change it.

- **Older rehearsal projects** are hidden by a UI filter ("latest rehearsal only"). There is no new `archived` status.
- **The golden project** (ADR 0012 item 2) is a `STANDARD` project **built once, by hand, through the real flow** with **stock voices only** (fixes M4, option a). It has no VoiceProfile, no Consent and no cloned audio. A real Reviewer reviews it and a real Localization Manager approves and exports it, so every Review, Approval and Export row and every audit record is genuine. It is **never reset or rebuilt**; `demo_reset` doesn't touch it. In the demo it shows completed review, approval, export, audit and evidence without calling any API. Because it holds no identity, a misclick in it can't withdraw anything, and the interim rule (no real voice in the golden project) becomes permanent. It is `STANDARD`, so the "latest rehearsal only" filter doesn't hide it.

### 3. Reset rebuilds and never restores

There are three commands. **Each one first takes `select_for_update()` on every IdentityOwner involved, in the global lock order (ADR 0003), with several IdentityOwners locked in **ascending id order** (fixes M3), and makes every check below under that lock** (fixes N1). So a withdrawal that commits first makes the command refuse, and a withdrawal that waits for the lock runs afterwards and purges what the command created.

**`manage.py build_demo_seed`** builds the demo seed from an approved project:
- the script, the approved translations and the stock-voice settings, as JSON;
- the reference clip;
- any pre-rendered cloned audio (when the demo plan pre-renders; *spike note: Plans B, C and D*).

It refuses unless (a) the owner's latest standing version is ACTIVE, unexpired, permits both `STANDARD` and `DEMO_REHEARSAL`, and its `uses` include `voice_synthesis` and its `languages` include the seed's language; and (b) the source project's consent scope passes the full gate under the lock, and none of the copied artefacts is `QUARANTINED`, `PURGED` or deletion-pending. It registers every seed file as an `OfflineCopy`. Audit: `SEED_BUILT`, or `SEED_BUILD_REFUSED` with the reason (written in its own transaction, like `DEMO_RESET_REFUSED`).

**`manage.py demo_reset`** never overwrites the database, deletes rows or restores files.

It **refuses** (audit: `DEMO_RESET_REFUSED`, with the reason) if:
- any identity owner in the seed is withdrawn; or
- an owner's latest standing version isn't ACTIVE, is expired, doesn't permit both `STANDARD` and `DEMO_REHEARSAL`, or lacks `voice_synthesis` or the seed's language in `uses` / `languages`; or
- a seed file it needs has **no** `OfflineCopy` row, a row that isn't `PRESENT`, or a SHA-256 that doesn't match its row.

Otherwise it does the following, in one transaction under the lock:
- creates a **new** `DEMO_REHEARSAL` project, "Demo (reset <timestamp>)";
- creates a derived Consent version for that project (§1) with **uses = parent.uses ∩ {`voice_synthesis`}**, languages = the seed's language, processors = parent.processors without **remote voice processors** (processors that receive the reference clip or produce cloned audio off the laptop; in the MVP that is Kaggle only. Text-only processors such as the translation LLM are not affected), and expires_at = parent.expires_at. A rehearsal project therefore can never use `remote_voice_processing` (fixes final-review B1);
- **copies** the seed reference clip to a new storage key and creates a new VoiceProfile through the normal gate (CP1). The project's revocation purges that copy, never the seed;
- imports pre-rendered cloned audio as new copies through the normal locked save (CP5);
- writes `DEMO_RESET` and `CONSENT_GRANTED (reason: DEMO_RESET, parent_consent_id)` audit records.

A rehearsal project starts with **no** Approval or Export. Review, approval and export in a rehearsal are done live, by real people, as part of the demo.

**`manage.py register_offline_copy`** registers a screen recording (§4). It refuses unless the owner's latest standing version is ACTIVE, **unexpired**, includes `voice_synthesis`, and its `permitted_copy_kinds` include `SCREEN_RECORDING`. Audit: `OFFLINE_COPY_REGISTERED`.

**Run the evening before:** `check_providers` and a trial `demo_reset`, so that a refusal surfaces then and not on demo morning. The stock-voice-only plan (SPIKE_PLAN §6) is the fallback if the reset refuses.

### 4. `OfflineCopy` register (parallel to ADR 0014's `RemoteCopy`)

**Fields:** identity_owner, `consent_version` (the standing version it was registered under; fixes N7), kind, storage_key (under `media/offline/`), sha256, created_at, deleted_at, status (`PRESENT` / `DELETION_PENDING` / `DELETED`). The kinds are:
- `DEMO_SEED_REFERENCE`;
- `DEMO_SEED_CLONED_AUDIO`;
- `SCREEN_RECORDING`.

Audit: `OFFLINE_COPY_REGISTERED` and `OFFLINE_COPY_DELETED`.

**One screen recording per speaker.** Each recording contains only one real speaker's cloned voice; anyone else in it uses a stock voice. So one speaker's withdrawal never deletes another speaker's recording.

**No backups of the demo stack** (simplification: there is no `DB_BACKUP` kind):
- no `pg_dump`, volume copy or other database or media backup is made of the demo stack;
- a backup made anyway breaks this rule. It goes on the manual withdrawal checklist (§6) and is deleted;
- a backup is never restored into the demo stack, and the system offers no restore command;
- if the stack is rebuilt on another machine after a failure, it starts with an empty database and a new audit chain, built from the seed. The golden project is then **built again by hand through the real flow**, with a new real approval. This is said openly in the demo.

**Drift warnings.** `check_providers` (ADR 0012 item 1) warns about:
- any file in `media/offline/` that has no `OfflineCopy` row;
- any file under `media/` whose SHA-256 matches a `DELETED` `OfflineCopy` or `VoiceProfile` hash (ADR 0006 keeps hashes after the purge).

These are **warnings for accidental drift, not tamper resistance**. A re-encoded or edited copy has a different hash and is not detected.

### 5. Revocation, narrowing and withdrawal: one path

**Scope revocation (amends ADR 0006 §5).**
- The cascade now covers **only** artefacts saved under a Consent version **in the revoked scope** (same owner, use and project), and only VoiceProfiles whose `consent` is in that scope. Other projects of the same owner are untouched.
- The purge also deletes the files of quarantined `RenderedScene`s (audio and video), and the package files of exports marked `CONSENT_REVOKED`. These are marked with a new status, `PURGED`.
- The rest of ADR 0006 §5 is unchanged.

**What counts as a real withdrawal.** This matches consent form Part D as amended for N4.

| Action | Effect |
|---|---|
| Revocation inside a `DEMO_REHEARSAL` project (on stage or in a team rehearsal) | **Demonstration only.** Scope revocation for that project; the next reset derives a fresh grant. The UI there says: "This revokes only this rehearsal project. To withdraw for real, use *Withdraw* on your consent page." |
| Revocation inside a `STANDARD` project | **Real, for that project only.** Nothing re-grants it automatically. It does **not** change the standing consent, the demo seed or the screen recording. The revoke dialog says: "This ends the use of your voice in this project only. To remove a use or withdraw everything, change your standing consent or press *Withdraw* on your consent page, or tell the withdrawal contact." *(For the spike speakers, "change your standing consent" means unticking a Part D use, as the consent form says.)* (fixes M2) |
| A new standing version that removes uses, purposes, copy kinds, languages or processors (partial withdrawal; for the spike speakers, unticking a Part D use) | **Real**, for what was removed: narrowing, below. |
| *Withdraw* (owner-level, all uses) | **Real and final**: narrowing to nothing, below. |

**Narrowing: the single withdrawal path** (fixes N2; simplification). A new standing version that narrows anything (uses, permitted purposes, permitted copy kinds, languages, processors, or an earlier `expires_at`), or a withdrawal, runs **one** procedure. In one transaction, under the IdentityOwner lock (ADR 0006 §4):
1. Insert the new standing version, with the narrowed `uses`, `permitted_purposes`, `permitted_copy_kinds`, `languages`, `processors` or `expires_at`, or with status `REVOKED` for a withdrawal.
2. For **every** project scope of that owner, `STANDARD` and `DEMO_REHEARSAL` alike, that no longer passes the gate, run the ADR 0006 §5 cascade. That inserts a REVOKED version, cancels or flags jobs, quarantines artefacts, invalidates approvals, marks exports and queues the purge. Removing `remote_voice_processing` therefore revokes it everywhere, including `STANDARD` projects (for the spike speakers: unticking D4). This stops future remote work and deletes our remote copies (ADR 0006 `RemoteCopy`; Kaggle's internal retention is outside our control, §6). It does **not** delete cloned audio already imported, which was saved under `voice_synthesis`; that goes only if `voice_synthesis` is removed or on withdrawal.
3. Mark the owner's `OfflineCopy` rows `DELETION_PENDING` for what was removed: a removed copy kind → the copies of that kind; `STANDARD` or `DEMO_REHEARSAL` removed from `permitted_purposes` → `DEMO_SEED_*` (the seed is useless without both); `voice_synthesis` removed from `uses`, or a copy's language removed from `languages` → every affected `OfflineCopy` of that owner; withdrawal → all.
4. For a withdrawal, also set `IdentityOwner.withdrawn_at`, `withdrawn_by` and `withdrawal_evidence`.

The purge then deletes the files, with the same "deletion pending" retry and audit behaviour (ADR 0006 §5).

**Who can narrow or withdraw:**
- the owner, from their own account; **or**
- an Administrator acting on a §8 request, who must record the request reference (who received it, when, and through which channel) as evidence. This records a decision the owner has already made; it can never widen anything.

The team names at least two people who can record a §8 withdrawal, so a same-day stop doesn't depend on one person. The names go on the paper form, not in git.

**Audit** (fixes N5):
- A narrowing writes `CONSENT_REVOKED`, with the actor being the owner, or the Administrator plus the request reference. Its details hold `removed: {field: values}` (any of uses, permitted purposes, permitted copy kinds, languages, processors, and the old and new `expires_at`) and the new standing version. Granting a standing consent, or widening it, writes `CONSENT_GRANTED` (kind `STANDING`, with the signed form ID as evidence). It also writes one `CONSENT_REVOKED` per cascaded project scope.
- A withdrawal additionally writes `IDENTITY_WITHDRAWN`. Its `consent_version` is the final standing version, and its details list every revoked version and the request reference.

**Withdrawal is final.** It **can't be undone** in the system. A speaker who comes back needs a new paper form and a new IdentityOwner.

**Expiry (amends the ADR 0006 expiry sweep).** When a standing grant expires, the sweep runs the same narrowing procedure (to nothing) with reason `EXPIRED`. Every project scope is cascaded, every `OfflineCopy` is purged, and the reset refuses. This matches the consent form's Part D end date.

### 6. What stays outside the system's reach

These are stated in the docs and the consent form, and are covered by a **manual withdrawal checklist** run by the person who records the withdrawal and logged in the spike log:
- **Part D copies kept in `~/hl-spike-media/`** (consent form §6), outside the system's media folder (fixes N6). Before the first system build, any Part D copy the system needs is brought in through `build_demo_seed` or `register_offline_copy`. Everything left in `~/hl-spike-media/` is deleted by hand on withdrawal, narrowing or expiry;
- any backup made in breach of §4;
- copies the system never saw (USB sticks, phones, someone filming the demo);
- export packages copied off the laptop, which **cannot be recalled** (ADR 0006 §7);
- Kaggle's internal retention;
- audio already sent to Groq;
- a manual database restore made outside the system. It would cut the audit chain. That is detectable only against a chain head copied out earlier, for example inside an export (ADR 0007).

### 7. Audit (amends ADR 0007's action list and ADR 0014 invariant 6)

New actions: `SEED_BUILT`, `SEED_BUILD_REFUSED`, `DEMO_RESET`, `DEMO_RESET_REFUSED`, `OFFLINE_COPY_REGISTERED`, `OFFLINE_COPY_DELETED` and `IDENTITY_WITHDRAWN`. `CONSENT_GRANTED` gains a reason, `DEMO_RESET`, plus `parent_consent_id`. `CONSENT_REVOKED` gains `removed: {field: values}` for a narrowing, and the reason `EXPIRED` for the sweep.

Each record carries who, what, when, project (where there is one) and consent version, as ADR 0007 requires. `DEMO_RESET_REFUSED` and `SEED_BUILD_REFUSED` have no action to share a transaction with, so each is written in its own transaction.

**Invariant 6** becomes: "Every audited action writes **at least one** AuditRecord, in the same transaction."

### 8. Data model changes (amends ADR 0014)

| Entity | Change |
|---|---|
| Project | + `purpose` (`STANDARD` / `DEMO_REHEARSAL`) |
| Consent | + `kind` (`PROJECT` / `STANDING`), + `parent_consent` (required for every `PROJECT` version in the MVP), + `permitted_purposes[]` and `permitted_copy_kinds[]` (standing only); `project` is null only for `STANDING`; `processors[]` applies to both kinds |
| IdentityOwner | + `withdrawn_at`, `withdrawn_by`, `withdrawal_evidence` |
| Export | status + `PURGED` |
| RenderedScene | the purge deletes the `audio_key` and `video_key` files (status `PURGED` already exists) |
| **OfflineCopy** | new model (§4) |

**New invariant 8:** every file in `media/offline/` has an `OfflineCopy` row, and every `PROJECT` Consent version has a parent standing version and is no wider than it (uses, languages, processors, `expires_at`).

### 9. Tests (19)

1. A reset never changes or removes existing `AuditRecord` rows (the chain prefix hash is the same before and after).
2. A reset refuses a withdrawn owner, and a standing consent that doesn't permit both purposes or has expired.
3. A reset refuses a seed file whose hash doesn't match, that has no row, or whose row is `DELETION_PENDING` or `DELETED`.
4. **Withdraw vs. reset concurrency, both orders:** no live copy of a withdrawn voice remains afterwards.
5. A revocation in one rehearsal project leaves the owner's other projects, and the seed reference clip, untouched.
6. Removing `DEMO_REHEARSAL` **or** `STANDARD` from `permitted_purposes` cancels running jobs and quarantines artefacts in every rehearsal project, purges the demo seed, makes the next reset refuse, and refuses an in-flight CP5 save that commits after the narrowing. Removing `STANDARD` also cascades every `STANDARD` project. An owner with no standing consent fails the gate.
7. Removing `SCREEN_RECORDING` from `permitted_copy_kinds` purges only that owner's `SCREEN_RECORDING` copies.
8. Removing `remote_voice_processing` (or the Kaggle processor) revokes it in every project scope, including `STANDARD`. Removing a language or a processor from the standing grant cascades every project scope that uses it (M1).
9. Withdrawal purges every `OfflineCopy`, export package and render file (including the `DELETION_PENDING` retry).
10. After withdrawal, the gate refuses every use × scope.
11. A `PROJECT` consent without a parent is refused, and so is one wider than its parent (uses, languages, processors, `expires_at`). A project version that was within an earlier standing version but is wider than the latest one fails the gate (M1). A widening standing version without a new paper form ID is refused (M5).
12. The Administrator can't create a standing grant, or any project consent except through a reset derivation.
13. Standing-grant expiry cascades every project scope, purges the `OfflineCopy` rows and blocks the reset.
14. `check_providers` warns about an unregistered file in `media/offline/`, and about a file whose hash matches a deleted copy.
15. `register_offline_copy` refuses a `SCREEN_RECORDING` that the standing consent doesn't permit; `demo_reset` never modifies the golden project; and a project with a VoiceProfile, Consent or cloned audio can't be named as the golden project: `check_providers` reads the `GOLDEN_PROJECT_ID` setting (environment variable) and warns if that project uses any identity.
16. Every new action writes its audit record with the required fields.
17. A derived rehearsal consent never contains `remote_voice_processing` or a remote processor, even when the parent does (B1).
18. Removing only `voice_synthesis` (or the seed's language) marks every affected `OfflineCopy` `DELETION_PENDING`, and the next `demo_reset` writes `DEMO_RESET_REFUSED`.
19. `build_demo_seed` refuses a source project whose consent scope fails the gate, or whose artefacts are quarantined, purged or deletion-pending.

### 10. Revocation demo (amends ADR 0012)

Under ADR 0011 only the owner revokes in the system, so the speaker must be **present and logged in** for the live revocation demo (fixes N8). If they can't be, the team says so and uses the agreed fallback in ADR 0006 §9 (running the deterministic checkpoint tests on screen). Nobody revokes on the speaker's behalf.

**No Kaggle path in rehearsal projects** (final-review B1). A derived rehearsal consent never includes `remote_voice_processing` (§3), so ADR 0006 §9's Kaggle-dispatched fallback **is not available** in a rehearsal project. If a live local job is not possible, the fallback is the deterministic checkpoint tests on screen.

## Weaknesses and edge cases

- **The register only covers what it is told about.** A screen recording or backup that nobody registers is invisible to the purge. The hash check catches only exact copies. Mitigations: the `check_providers` warnings, a fixed folder, the no-backup rule and the manual checklist (§6). It still depends on people.
- **The rehearsal-vs-real rule depends on where the owner clicks.** A revocation inside a rehearsal project is always treated as a demonstration, even if the owner meant it for real. Mitigations: the UI text in §5, the *Withdraw* button on the owner's consent page, and the consent form wording (N4, applied 2026-10-06).
- **Re-deriving consent on every reset could look like consent theatre.** Answer for the viva: the owner granted a standing consent once, in their own account. Each reset makes an audited, project-only copy that can't be wider than that grant. Removing a demo purpose, or withdrawing, blocks every future reset.
- **The demo seed is a second copy of the reference clip** for as long as the demo exists. This is deliberate: it is registered, hashed, purged on narrowing, withdrawal or expiry, and covered by the standing consent (for the spike speakers, consent form Part D).
- **Locking several owners in one command** relies on locking them in ascending id order to avoid deadlocks. The demo has at most two owners.
- **The database fills with rehearsal projects.** That is acceptable for a demo; the UI filter hides them.
- **Scope:** 1 model, about 8 fields, 3 commands and 19 tests [ESTIMATE: about 2–3 days, the reviewer's figure, not measured]. If the build runs short, the fallback is **no cloned voice in any demo project** (stock-only demo, SPIKE_PLAN §6).
- **Spike phase:** there is no system yet. During the spike, withdrawal is done by hand and logged in the spike log (consent form §8). This ADR applies from the first system build. Until it is approved, the interim rule applies: no real voice in any demo seed or golden project.

## Consequences

- **+** The consent form §8 promise is **designed to be enforced** by the code for registered copies inside the system's media folder, and by the manual checklist for everything else (§6). It becomes [CONFIRMED] only when tests 4–9 pass.
- **+** The system offers no restore operation, so the system itself never cuts the audit chain. A manual restore remains a residual risk (§6).
- **+** The difference between a demonstration revocation and a real withdrawal is defined by the project's purpose and is **designed to be enforced** in the gate and the locked saves.
- **+** ADR 0011's rule holds: only the owner grants; the system derives narrower copies; an Administrator only records a withdrawal or narrowing that the owner asked for, with evidence.
- **+** The golden project holds no identity, so it is always safe to show and can't be damaged by a misclick. Its approval is a real human approval, made once, so "who approved this?" has a true answer.
- **−** More model and gate logic: a standing grant kind, a required parent link and a purpose flag. **UML diagrams to update:** class diagram (OfflineCopy plus the new fields), Consent states (standing and project versions, narrowing), UC7 activity or sequence diagram (narrowing and withdrawal).
- **−** Rehearsal discipline is still needed for screen recordings and backups.
- **Viva in 2 minutes:** "The speaker grants a standing consent once, in their own account. Every project consent is a copy of that grant that can't be wider. A demo reset builds a fresh rehearsal project and makes such a copy, and the audit log only grows. Revoking inside a rehearsal project is the demonstration and affects only that project. Revoking anywhere else, narrowing the standing consent, or pressing *Withdraw* is real. It goes through one procedure that revokes every affected project, deletes the registered copies and blocks future resets. Admins can't grant consent; they can only record a withdrawal the speaker asked for. The golden project uses stock voices and was reviewed and approved once by real people, so it holds nobody's identity."
