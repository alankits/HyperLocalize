# ADR 0020: Demo reset by rebuild, offline-copy register, and identity withdrawal

**Status:** **Proposed** (2026-10-06), waiting for approval. **Revision 2** (2026-10-06): all 14 findings of the independent review (`docs/adr/0020-REVIEW.md`) applied at the user's request. If approved, it **amends** these ADRs, which are not edited until then:
- ADR 0006: §1 (the gate), §5 (cascade scope, purge, expiry sweep);
- ADR 0007: the list of audited actions;
- ADR 0011: the Administrator and Identity Owner rows, and the viva line;
- ADR 0012: demo-resilience items 1 (`check_providers`), 2 (golden project), 3 (screen recording) and 7 (demo reset);
- ADR 0014: Project, Consent, IdentityOwner, Export, the new `OfflineCopy` model, invariant 6, and a new invariant 8.

**Source:** consent review #2 (`docs/spike/CONSENT_FORM_REVIEW.md`); `docs/STATUS.md` known issues; ADRs 0006, 0007, 0011, 0012, 0014; consent form §6, §8 and Part D.

## Context

ADR 0012 item 7 says: "`manage.py demo_reset` restores a database and media snapshot of the prepared project before each rehearsal and the final demo." It is needed because the live revocation demo purges the reference clip, so every rehearsal uses up the demo state. Read against the other accepted ADRs and the revised consent form, this causes four problems. Problems 1, 2 and 4 are [CONFIRMED] from the ADR text. Problem 3 is [INFERRED]: restoring a whole-database snapshot taken at time T loses every row added after T, whatever tool does the restore.

1. **Withdrawal can't reach the snapshot.** ADR 0006's purge deletes cloned audio, the VoiceProfile clip and the Kaggle copies. It doesn't know about the snapshot, the pre-rendered seed audio, export package files or the backup screen recording (ADR 0012 item 3). But consent form §8 now promises that withdrawal deletes "the demo reset snapshot, the golden (pre-prepared) demo project, export packages, the backup screen recording … and any copy in the HyperLocalize system".
2. **A restore brings a revoked speaker back.** Restoring a database snapshot puts back the old ACTIVE Consent rows, so a speaker who really withdrew would be "un-revoked" by the next rehearsal.
3. **A restore silently cuts the audit history.** ADR 0007's triggers block `UPDATE`, `DELETE` and `TRUNCATE` on `AuditRecord`, but a database restore replaces the table and bypasses them. Every audit record written after the snapshot is lost, possibly including a real withdrawal. The records that remain still form a valid chain, so the verifier can't detect the cut (ADR 0007's threat table: detection works only for records older than a chain head copied out earlier).
4. **ADR 0006 §5 revocation is owner-wide.** It quarantines "every `SynthesisedSegment` and `RenderedScene` recorded under that owner's consent" and purges "the VoiceProfile reference clip". So an on-stage revocation would also wipe the golden project.

**Constraints:**
- zero budget; a small team with little DevOps experience (Q2);
- rehearsals must stay quick;
- the live revocation demo must still really revoke in the system;
- the demo revocation must not end the speaker's real consent (consent form D2), but a **real** withdrawal (consent form Part D, P5) must be final;
- ADR 0011: only the identity owner can grant consent, and the Administrator **cannot grant consent on anyone's behalf**.

## Options Considered

| Criterion | **A. Keep the snapshot; manual withdrawal checklist** | **B. Keep the snapshot; register it and guard the restore** | **C. Rebuild, don't restore: owner's standing grant, derived demo grants, offline-copy register, owner-level withdrawal** | **D. No reset: rerun the real flow before each rehearsal** |
|---|---|---|---|---|
| Keeps the §8 promise (withdrawal deletes all copies) | Only if a person remembers | Yes, for registered copies | **Yes, in code, for registered copies** | Yes (there are no extra copies) |
| A real withdrawal can't be undone by a reset | **No**: the restore brings back ACTIVE consent | Yes, if the guard works | **Yes**: the reset refuses a withdrawn owner or a withdrawn D1/D2 | Yes |
| Audit integrity (ADR 0007) | **Broken**: the restore cuts the chain silently | **Broken**: same | **Kept by the system**: the reset only appends. A manual restore remains a residual risk (§6) | Kept |
| Consistent with ADR 0011 (only the owner grants) | Depends on who restores | Same | **Yes**: the owner grants once; the reset only derives narrower, project-only versions | Yes, but the owner must re-grant before every rehearsal |
| Rehearsal reliability | High | High | High (once the seed exists) | **Low**: needs the speaker and, under Plans C/D, an overnight render for every rehearsal |
| Privacy (copies outside the purge) | Snapshot and recording unmanaged | Registered, purged | Registered, purged | None |
| Data model change | None | +1 model | +1 model, about 8 fields | None |
| Effort [ESTIMATE] | Very low | Low–medium | **Medium**: 1 model, about 8 fields, 3 commands, about 15 tests (about 3–4 days) | Low code, high rehearsal time |
| Cost | ₹0 | ₹0 | ₹0 | ₹0 |
| Scalability | Demo-only in every option | | | |
| Viva: explain in 2 minutes | Easy to explain, hard to defend | Hard to defend ("your reset deletes audit records") | **Moderate**: "the speaker grants once; each reset makes a project-only copy; revoking in a rehearsal is the demo, revoking anywhere else is real" | Easy, but the demo is fragile |

## Decision (proposed)

**Option C.**

### 1. The owner's standing grant, and derived demo grants

**Standing grant** (fixes review #1).
- The Speaker / Identity Owner signs in with their own account (ADR 0011, Q10) and grants **one** Consent version of a new kind, `STANDING_PART_D`. It records:
  - `part_d_uses[]`: the Part D ticks, any of `D1_DEVELOPMENT`, `D2_LIVE_DEMO`, `D3_SCREEN_RECORDING`, `D4_KAGGLE`;
  - `uses[]`: `voice_synthesis`, plus `remote_voice_processing` only if D4 is ticked;
  - `languages[]`;
  - `expires_at`: **no later than the Part D end date** (fixes #7);
  - evidence: the paper form ID and version;
  - `granted_by`: the owner's own user.
- It has no project. **The gate never accepts it directly.** Its only role is to authorise derived versions.
- Changing it means the owner grants a new version; the latest version is current (ADR 0014).

**Derived grants.** Each `demo_reset` run creates, in the new demo project, a project-scoped Consent version with:
- `parent_consent` = the latest standing version;
- `uses ⊆ parent.uses`;
- `languages ⊆ parent.languages`;
- `expires_at ≤ parent.expires_at`;
- `granted_by` = system (`DEMO_RESET`), with the Administrator who ran the command recorded as `triggered_by` in the audit details.

The derived version can only be **narrower** than what the owner granted. The Administrator triggers the copy but can't create, widen or extend consent.

**Gate change (amends ADR 0006 §1).** `require_active_consent` also returns false if:
- `IdentityOwner.withdrawn_at` is set; or
- the version has a `parent_consent` whose latest version is not ACTIVE, is expired, or doesn't contain the Part D use the project needs. Rehearsal and golden projects need `D1_DEVELOPMENT` and `D2_LIVE_DEMO`. `remote_voice_processing` needs `D4_KAGGLE`.

These are extra conditions in the same gate, not a new gate.

**Which tick covers what** (fixes #12): team rehearsals are covered by **D1** (development and testing on the team laptop, heard by the team, R1 and R2). The panel and audience are covered by **D2**. The reset therefore requires **both**.

### 2. Project purpose (fixes #3 and #11)

A new field, `Project.purpose`, takes one of three values: `STANDARD` (the default), `DEMO_REHEARSAL` or `DEMO_GOLDEN`. The two demo values are set **only** by `demo_reset`; no API or UI can set or change them.
- **`DEMO_REHEARSAL`:** a project built for one rehearsal or the live demo.
- **`DEMO_GOLDEN`:** the golden project (ADR 0012 item 2), now defined as a project built by `demo_reset --golden` from the same seed (fixes #4). It shows completed review, approval, export, audit and evidence without calling any API.
- **Older rehearsal projects** are hidden by a UI filter ("latest rehearsal only"). There is no new `archived` status.

### 3. Reset rebuilds and never restores

There are three commands (fixes #10):

**`manage.py build_demo_seed`** builds the demo seed from an approved project:
- the script, the approved translations and the stock-voice settings, as JSON;
- the reference clip;
- any pre-rendered cloned audio (Plans B, C and D).

It refuses unless the owner's standing grant is ACTIVE with D1 and D2, and it registers every seed file as an `OfflineCopy`. Audit: `SEED_BUILT`.

**`manage.py demo_reset [--golden]`** never overwrites the database, deletes rows or restores files. It **refuses** (audit: `DEMO_RESET_REFUSED`, with the reason) if:
- any identity owner in the seed is withdrawn; or
- an owner's latest standing version isn't ACTIVE, is expired, or lacks D1 or D2; or
- the date is past any owner's standing `expires_at`; or
- a seed file has **no** `OfflineCopy` row, a row that isn't `PRESENT`, or a SHA-256 that doesn't match its row (fixes #6).

Otherwise it does the following, in one transaction:
- creates a **new** project, "Demo (reset <timestamp>)", with purpose `DEMO_REHEARSAL` (or `DEMO_GOLDEN`);
- creates a derived Consent version for that project (§1);
- **copies** the seed reference clip to a new storage key and creates a new VoiceProfile through the normal gate (CP1). The demo purge deletes that copy, never the seed (fixes #2);
- imports pre-rendered cloned audio as new copies through the normal locked save (CP5), so the consent check still applies;
- writes `CONSENT_GRANTED (reason: DEMO_RESET, parent_consent_id)` and `DEMO_RESET` audit records.

**`manage.py register_offline_copy`** registers a file made outside the system (§4).

**Run the evening before:** `check_providers` and a trial `demo_reset`, so that a refusal surfaces then and not on demo morning. The stock-voice-only plan (SPIKE_PLAN §6) is the fallback if the reset refuses.

### 4. `OfflineCopy` register (parallel to ADR 0014's `RemoteCopy`)

**Fields:** identity_owner, kind, storage_key (under `media/offline/`), sha256, created_at, deleted_at, status (`PRESENT` / `DELETION_PENDING` / `DELETED`). The kinds are:
- `DEMO_SEED_REFERENCE`;
- `DEMO_SEED_CLONED_AUDIO`;
- `SCREEN_RECORDING`;
- `DB_BACKUP`.

Audit: `OFFLINE_COPY_REGISTERED` and `OFFLINE_COPY_DELETED`.

**Screen recordings** (ADR 0012 item 3) are made outside the system and registered with `register_offline_copy`.
- Registration is refused unless the owner's latest standing version includes `D3_SCREEN_RECORDING`.
- **One recording per speaker** (fixes #13): each recording contains only one real speaker's cloned voice, and any other speaker in it uses a stock voice. So one speaker's withdrawal never deletes another speaker's recording.

**No backups of the demo stack** (fixes #5):
- no `pg_dump`, volume copy or other database or media backup is made of the demo stack;
- any that is made anyway must be registered as `DB_BACKUP`, with one row per identity owner present. Withdrawal of any of them deletes the file, and every row with that storage key is marked `DELETED`;
- a backup is **never restored** into the demo stack. The system offers no restore command;
- if the stack is rebuilt on another machine after a failure, it starts with an empty database and a new audit chain, built from the seed. This is said openly in the demo, not hidden.

**Drift checks.** `check_providers` (ADR 0012 item 1) and `demo_reset` both:
- warn about any file in `media/offline/` that has no `OfflineCopy` row;
- flag any file anywhere under `media/` whose SHA-256 matches a `DELETED` `OfflineCopy` or `VoiceProfile` hash (ADR 0006 keeps hashes after the purge).

This is **accidental-drift detection, not tamper resistance**. A re-encoded or edited copy has a different hash and is not detected.

### 5. Revocation vs. withdrawal

**Scope revocation (amends ADR 0006 §5; fixes #2).**
- The cascade now covers **only** the artefacts saved under a Consent version **in the revoked scope** (same owner, use and project), and only VoiceProfiles whose `consent` is in that scope. Other projects of the same owner are untouched.
- The purge also deletes the files of quarantined `RenderedScene`s (audio and video), and the package files of exports marked `CONSENT_REVOKED`. These are marked with a new status, `PURGED` (fixes #4).
- The rest of ADR 0006 §5 is unchanged.

**What counts as a real withdrawal** (matches consent form Part D, P5; fixes #3). Any of these:

| Action | Effect |
|---|---|
| Revocation inside a `DEMO_REHEARSAL` project | **Demonstration only.** Scope revocation for that project. The next reset derives a fresh grant. The UI on these projects says: "This revokes only this rehearsal project. To withdraw for real, use *Withdraw* on your consent page." |
| Revocation inside a `STANDARD` project | **Real**, for that project. Nothing in the system re-grants it; only the owner can grant a new version. |
| Revocation inside the `DEMO_GOLDEN` project | **Real withdrawal of D2.** The system creates a new standing version without D2, so every demo project's derived grant fails the gate, and the reset refuses. |
| New standing version without one or more Part D uses (partial withdrawal, §8 "any or all") | For each removed use: **D1** revokes the owner's scope in every `STANDARD` project, in the same transaction (ADR 0006 cascade). Those grants are the owner's own and have no parent link, so the gate alone wouldn't catch them; **D2** is as above; **D3** marks only the owner's `SCREEN_RECORDING` copies `DELETION_PENDING`; **D4** revokes `remote_voice_processing` in every derived scope (ADR 0006 cascade, `RemoteCopy` deletion). |
| *Withdraw* (owner-level, all uses) | See below |

**Owner-level withdrawal.**
- **Who:** the owner, from their own account; **or** an Administrator acting on a §8 request, who must record the request reference (who received it, when, and through which channel) as evidence. This records a decision the owner has already made; it never grants anything. The team names at least two people who can record a §8 withdrawal, so a same-day stop doesn't depend on one person (fixes #14). The names go on the paper form, not in git.
- **Records:** `IdentityOwner.withdrawn_at`, `withdrawn_by` and `withdrawal_evidence` (new fields), and an `IDENTITY_WITHDRAWN` audit record. Its `consent_version` is the owner's last standing version, and its details list every revoked version and the request reference (fixes #8).
- **Transaction:** in one transaction, under the IdentityOwner lock (ADR 0006 §4), it:
  - revokes **every** scope, including the standing grant, writing a `CONSENT_REVOKED` record for each;
  - runs the scope cascade for each;
  - marks every `OfflineCopy` of that owner `DELETION_PENDING`.
- **Purge:** deletes those files, export packages and render files, with the same "deletion pending" retry and audit behaviour (ADR 0006 §5).
- **Final:** withdrawal **can't be undone** in the system. A speaker who comes back needs a new paper form and a new IdentityOwner.

**Expiry (amends the ADR 0006 expiry sweep; fixes #7).** When a standing grant expires:
- every derived version fails the gate (parent expired), and the sweep runs the cascade for them;
- every `OfflineCopy` of that owner is marked `DELETION_PENDING` and purged.

This matches the consent form's Part D end date.

### 6. What stays outside the system's reach

These are stated in the docs and the consent form:
- copies the system never saw (USB sticks, phones, someone filming the demo, unregistered backups);
- export packages copied off the laptop, which **cannot be recalled** (ADR 0006 §7);
- Kaggle's internal retention;
- audio already sent to Groq;
- a manual database restore made outside the system. It would cut the audit chain. That is detectable only against a chain head copied out earlier, for example inside an export (ADR 0007).

### 7. Audit (amends ADR 0007's action list and ADR 0014 invariant 6)

New actions: `SEED_BUILT`, `DEMO_RESET`, `DEMO_RESET_REFUSED`, `OFFLINE_COPY_REGISTERED`, `OFFLINE_COPY_DELETED` and `IDENTITY_WITHDRAWN`. `CONSENT_GRANTED` gains a reason, `DEMO_RESET`, plus `parent_consent_id`.

Each record carries who, what, when, project (where there is one) and consent version, as ADR 0007 requires. `DEMO_RESET_REFUSED` has no action to share a transaction with, so it is written in its own transaction.

**Invariant 6** becomes: "Every audited action writes **at least one** AuditRecord, in the same transaction." A withdrawal writes `IDENTITY_WITHDRAWN` plus one `CONSENT_REVOKED` per scope.

### 8. Data model changes (amends ADR 0014)

| Entity | Change |
|---|---|
| Project | + `purpose` (`STANDARD` / `DEMO_REHEARSAL` / `DEMO_GOLDEN`) |
| Consent | + `kind` (`PROJECT` / `STANDING_PART_D`), + `parent_consent` (nullable), + `part_d_uses[]` (standing only); `project` is null only for `STANDING_PART_D` |
| IdentityOwner | + `withdrawn_at`, `withdrawn_by`, `withdrawal_evidence` |
| Export | status + `PURGED` |
| RenderedScene | the purge deletes `audio_key` and `video_key` files (status `PURGED` already exists) |
| **OfflineCopy** | new model (§4) |

**New invariant 8:** every file in `media/offline/` has an `OfflineCopy` row, and every derived Consent version is no wider than its parent (uses, languages, `expires_at`).

### 9. Tests

1. A reset never changes or removes existing `AuditRecord` rows (the chain prefix hash is the same before and after).
2. A reset refuses a withdrawn owner, and a standing grant that lacks D1 or D2 or has expired.
3. A reset refuses a seed file whose hash doesn't match, that has no row, or whose row is `DELETION_PENDING` or `DELETED`.
4. A revocation in a `DEMO_REHEARSAL` project leaves the golden project's consent, VoiceProfile and artefacts untouched, and leaves the seed reference clip in place.
5. A revocation in the `DEMO_GOLDEN` project removes D2, and the next reset refuses.
6. Partial withdrawal of D3 purges only that owner's `SCREEN_RECORDING` copies.
7. Withdrawal purges every `OfflineCopy`, export package and render file (including the `DELETION_PENDING` retry).
8. After withdrawal, the gate refuses every use × scope.
9. A derived version can't be wider than its parent.
10. The Administrator can't create a standing grant, or any Consent version except through a reset derivation.
11. Standing-grant expiry purges `OfflineCopy` rows and blocks the reset.
12. `check_providers` flags an unregistered file in `media/offline/`, and a file whose hash matches a deleted copy.
13. `register_offline_copy` refuses a `SCREEN_RECORDING` without D3.
14. Every new action writes its audit record with the required fields.

## Weaknesses and edge cases

- **The register only covers what it is told about.** A screen recording or backup that nobody registers is invisible to the purge. The hash check catches only exact copies. Mitigations: the `check_providers` warnings, a fixed folder, the no-backup rule and the demo-day checklist. It still depends on people.
- **The rehearsal-vs-real rule depends on where the owner clicks.** A revocation inside a rehearsal project is always treated as a demonstration, even if the owner meant it for real. Mitigation: the UI text in §5, and the *Withdraw* button on the owner's consent page. Proposed consent form tweak (needs approval, not applied): change "revoke your consent in the HyperLocalize system outside a demo" to "… outside a project marked *Demo rehearsal*".
- **Re-deriving consent on every reset could look like consent theatre.** Answer for the viva: the owner granted Part D once, in their own account. Each reset makes an audited, project-only copy that can't be wider than that grant. A real withdrawal, or removing D2, blocks every future reset.
- **The demo seed is a second copy of the reference clip** for as long as the demo exists. This is deliberate: it is registered, hashed and purged on withdrawal or expiry, and covered by consent Part D.
- **The database fills with rehearsal projects.** That is acceptable for a demo; the UI filter hides them.
- **This is more scope than revision 1:** 1 model, about 8 fields, 3 commands and about 14 tests [ESTIMATE: 3–4 days]. That is justified because the alternatives break accepted ADRs (0007, 0011) or a promise in the consent form. If the build runs short, the fallback is **no cloned voice in any demo project** (stock-only demo, SPIKE_PLAN §6). The interim rule stays in force.
- **Spike phase:** there is no system yet. During the spike, withdrawal is done by hand and logged in the spike log (consent form §8). This ADR applies from the first system build. Until it is approved, the interim rule applies: no real voice in any demo-reset snapshot or golden project.

## Consequences

- **+** The consent form §8 promise becomes something the code enforces for **registered** copies.
- **+** The system offers no restore operation, so the system itself never cuts the audit chain. A manual restore remains a residual risk (§6).
- **+** The difference between a demonstration revocation and a real withdrawal is defined by the project's purpose and is **designed to be enforced** in the gate. It becomes [CONFIRMED] only when tests 4–8 pass.
- **+** ADR 0011's rule holds: only the owner grants; the system derives narrower copies; an Administrator only records a withdrawal the owner asked for, with evidence.
- **−** More model and gate logic: a standing grant kind, a parent link and a purpose flag. The UML class diagram, the Consent state diagram and the UC7 activity or sequence diagram need updating. **UML diagrams to update: class diagram (OfflineCopy plus the new fields), Consent states (standing and derived), UC7 (the withdrawal and partial-withdrawal paths).**
- **−** Rehearsal discipline is still needed for screen recordings and backups.
- **Viva in 2 minutes:** "The speaker grants Part D once, in their own account. Each demo reset builds a fresh project and makes a project-only copy of that consent, never a wider one, and the audit log only grows. Revoking inside a rehearsal project is the demonstration and affects only that project. Revoking anywhere else, or pressing *Withdraw*, is real: it revokes everything, deletes every registered copy including the seed and the recording, and blocks any future reset. Admins can't grant consent; they can only record a withdrawal the speaker asked for."
