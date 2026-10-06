# Independent review: ADR 0020 (demo reset and identity withdrawal)

## Round 1 (revision 1)

| | |
|---|---|
| **Reviewed** | `docs/adr/0020-demo-reset-and-identity-withdrawal.md` as of commit `5f16834` (Proposed) |
| **Reviewer** | `critical-reviewer` agent (fresh context), 2026-10-06, at the user's request |
| **Context read** | ADRs 0006, 0007, 0011, 0012, 0014; `CONSENT_FORM.md` (§6, §8, Part D); `CONSENT_FORM_REVIEW.md` round 2. The reviewer may have read the consent form before the round-2 P1–P8 edits landed; this doesn't change any finding. |
| **Verdict** | **Needs changes:** 2 blockers, 6 major, 6 minor |
| **Status** | **Applied in revision 2** (2026-10-06, user chose "apply all, then re-review"). See round 2. |

The assistant checked both blockers against the files and found them accurate. ADR 0011 line 32 says the Administrator "**Cannot grant consent on anyone's behalf**". ADR 0006 §5 quarantines and purges everything "recorded under that owner's consent", including the VoiceProfile reference clip (lines 71 and 78), not just one project's scope.

Rebuilding instead of restoring is judged to be the right core idea.

## Problems

| # | Severity | Section | Problem | Proposed fix |
|---|---|---|---|---|
| 1 | **Blocker** | §1 "actor = the Administrator who ran the reset"; §3 withdrawal "by an Administrator" | This contradicts ADR 0011, where the Administrator cannot grant consent on anyone's behalf and only the identity owner can change consent. ADR 0011 isn't listed as amended. | The owner grants one standing in-system Part D consent themselves. Each reset creates a *derived* project-scoped version that references it (actor: system, reason: DEMO_RESET, `parent_consent_id`). Withdrawal is done by the owner, or by an Administrator only when acting on a logged §8 request (request reference stored as evidence). List ADR 0011 as amended. |
| 2 | **Blocker** | §3 "Scope revocation (ADR 0006 §5, unchanged)" | ADR 0006 §5 is owner-wide, so an on-stage revocation would also quarantine the golden project and purge the reference clip. Test 5 would fail. | Amend ADR 0006 §5 so the cascade covers only artefacts made under the revoked scope's consent versions, and only that scope's VoiceProfile. The reset *copies* the seed clip into a new VoiceProfile, so the demo purge never deletes the seed. |
| 3 | Major | §3 vs consent form P5 | Under P5, a revocation in the system outside a demo is a real withdrawal. Under ADR 0020 it is only a scope revocation, which the next reset re-grants. §8 allows withdrawing individual uses (only D2 or only D3, for example), but ADR 0020's withdrawal is all-or-nothing. | Add `Project.purpose = DEMO_REHEARSAL`, set only by `demo_reset`. A revocation of a Part D scope on any other project counts as a withdrawal of that use. Record the Part D ticks per use on the standing grant (#1). Reset refuses if D2 is withdrawn. A D3 withdrawal purges only `SCREEN_RECORDING`. |
| 4 | Major | §3, §4 | The purge never deletes export package files or RenderedScene video files; ADR 0006 only marks exports `CONSENT_REVOKED`. The consent form (P3) promises to delete exports and the golden project, but ADR 0020 doesn't define the golden project. | On withdrawal, delete export packages and render files and mark them PURGED. Define the golden project as a project built by the reset. Add "exports copied off the laptop cannot be recalled" to §4. |
| 5 | Major | §1, Consequences | "Never restores" describes only the command. `pg_dump`/`pg_restore`, a copied Docker volume or a home-folder backup can still restore. | Rule: no database or media backups of the demo stack; any that are made are registered as `OfflineCopy kind=DB_BACKUP`. Reword the consequence to "the system provides no restore path". |
| 6 | Major | §1 refusals, §2 | The SHA-256 check catches only a hash mismatch. It misses a seed file with no row or with a DELETED/DELETION_PENDING row, and a withdrawn file copied back in. | Reset refuses on missing, deleted or pending rows. `check_providers` and the reset flag any `media/` file whose hash matches a DELETED `OfflineCopy` (hashes are kept, per ADR 0006). Label the check "accidental-drift detection, not tamper resistance". |
| 7 | Major | §1, Weaknesses | Nothing caps a reset grant's `expires_at` at the Part D end date, and `OfflineCopy` deletion is triggered only by withdrawal, not by expiry. | Cap `expires_at` at the Part D end date, and make the reset refuse after it. The ADR 0006 expiry sweep marks the owner's `OfflineCopy` rows `DELETION_PENDING`. |
| 8 | Major | Audit (§1–§3) | Building the seed, `register_offline_copy`, a reset refusal and each `OfflineCopy` deletion have no audit record. `IDENTITY_WITHDRAWN` has no single consent version. Writing several records per withdrawal conflicts with ADR 0014 invariant 6 ("exactly one"). ADR 0007's action list isn't updated. | Add `SEED_BUILT`, `OFFLINE_COPY_REGISTERED`, `DEMO_RESET_REFUSED` and `OFFLINE_COPY_DELETED`. `IDENTITY_WITHDRAWN` details list the revoked versions and the §8 request reference. Amend invariant 6 to "at least one, in the same transaction". Amend ADR 0007. |
| 9 | Minor | Status line | The list of amended ADRs is incomplete. | Add ADR 0006 §1, ADR 0007, ADR 0011 and ADR 0012 §1–§3. Add an ADR 0014 invariant: every file in `media/offline/` has an `OfflineCopy` row. |
| 10 | Minor | Weaknesses "2 commands" | Nothing builds the seed. | Add `build_demo_seed` (3 commands). |
| 11 | Minor | §1 "marked archived" | ADR 0014's Project status has no archived value. | Define the value, or use the purpose flag from #3. |
| 12 | Minor | Weaknesses "D2 … authorises repeated demonstration revocations" | D2 covers the panel and audiences, not team rehearsals. | Cite D1 and D2, or add "and team rehearsals" to D2 (a consent form change, which needs approval). |
| 13 | Minor | §2 multi-speaker recording | When one speaker withdraws, the shared screen recording is deleted for everyone, possibly on the eve of the demo. | One recording per speaker, or say this in D3. |
| 14 | Minor | §3 | §8 promises a same-day stop, but withdrawal depends on an Administrator being available. | Name a deputy, or allow the owner to withdraw themselves (#1). |

## Honesty violations

- **"Audit history is append-only in practice … because no operation ever restores the database"** (Consequences). This overclaims, because a manual restore is still possible (#5). Fix: "the system offers no restore operation; a manual restore is a residual risk, detectable only against an exported chain head (ADR 0007)".
- **"The difference … is enforced in the backend"** (Consequences). This is premature while #2 and #3 are open. Fix: "designed to be enforced", or fix #2 and #3 first.
- **"D2 tick, which authorises repeated demonstration revocations"** (Weaknesses). The form text doesn't say this (#12).
- **Viva line: "re-grants consent from the signed form".** As written, the Administrator re-grants consent, which ADR 0011 forbids (#1).
- The status labels are used correctly, and the effort figure is marked [ESTIMATE]. The review found no use of "secure", "tamper-proof" or "guarantees".

## Demo and viva risks

- "ADR 0011 says admins can't grant consent. Who granted it here?" There is no defence as written; fix #1.
- "You revoked on stage. Did the golden project just lose its voice?" Under ADR 0006 as written, yes; fix #2 and run test 5 on screen.
- The reset refuses on demo morning (hash mismatch or a pending row). Run the reset and `check_providers` the evening before, and keep a stock-voice-only fallback.
- The laptop dies and the stack is rebuilt elsewhere. The seed rebuild works, but the audit chain starts from zero; say so openly.
- "Is a speaker who revokes in the app really out?" This needs the #3 rule, stated in one sentence.

## What the reviewer found good

- The analysis of why a restore fails is precise and tied to ADR 0007's threat table.
- Owner-level withdrawal is added as a second condition inside the existing gate, not as a new gate. It can't be undone, and a returning speaker gets a fresh IdentityOwner. This is simple and defensible.
- §4 states the system's limits plainly, and §5 lists concrete, checkable tests.

## Assistant's note (not part of the review)

The fixes for #1–#3 change the consent model (a standing owner grant, derived versions, a project purpose flag) and amend ADRs 0006, 0007, 0011 and 0014. They need the user's approval before ADR 0020 is revised. #12 would also change the consent form.

## Round 2 (revision 2, 2026-10-06)

| | |
|---|---|
| **Reviewed** | Revision 2 of ADR 0020 (all 14 round-1 fixes applied) |
| **Reviewer** | `critical-reviewer` agent (fresh context). It read ADRs 0006, 0011 and 0014, the consent form and round 1; it did not reread 0007 or 0012. |
| **Verdict** | **Approve with changes:** 0 blockers, 4 major, 3 minor. Text changes only, no redesign. |
| **Status** | **Applied in revision 3** (2026-10-06, with the user's approval of N1–N7, the simplification and the N4 form wording). See round 3. |

The assistant checked N1–N3 against the files and found them accurate:
- revision 2 §3 takes no IdentityOwner lock;
- the ADR 0006 §4 locked save re-reads only its own scope's latest version;
- `STANDARD` grants have no parent.

**Round-1 findings:**
- Fixed: #1, #2, #4–#6 and #9–#14.
- Partly fixed: #3 (N2, N4), #7 (N3) and #8 (N5).

| # | Severity | Section | Problem | Proposed fix |
|---|---|---|---|---|
| N1 | Major | §3, §4 commands | `demo_reset`, `build_demo_seed` and `register_offline_copy` take no IdentityOwner lock. If a withdrawal commits between the reset's check and its commit, the withdrawn voice is copied back with nothing queued to purge it. | All three `select_for_update()` the IdentityOwner first and re-check `withdrawn_at` and the latest standing version under the lock. Add a withdraw-vs-reset concurrency test, in both orders. |
| N2 | Major | §5 D2 and golden rows | Removing D2 makes derived grants fail the gate, but no cascade runs: running jobs aren't cancelled, artefacts aren't quarantined, and an in-flight CP5/CP7 save still succeeds because its own scope is still ACTIVE. | Any standing narrowing runs the ADR 0006 cascade, in the same transaction, on every scope that no longer passes. CP5, CP7 and CP9 call the full gate (parent and `withdrawn_at`) under the lock. Test: a save after D2 removal is refused. |
| N3 | Major | §1, §5 D1 and D4 rows | `STANDARD`-project grants have no parent. They aren't capped at the Part D end date, and removing D4 misses them. | Make **every** project consent derived from the standing grant (the owner grants in `STANDARD` projects, the system in demo projects; all must be ⊆ the parent). This removes the D1 special case. |
| N4 | Major | §5 vs consent form Part D | The form says a revocation "outside a demo" is real. The ADR treats any revocation in a rehearsal project, including team rehearsals, as not real. The form tweak is only proposed. | Approve the form tweak with this ADR, before any Part D signature, and make D2's text also cover rehearsals. |
| N5 | Minor | §1 vs §5 golden row, test 10 | "The system creates a new standing version" contradicts "granted_by: the owner" and test 10. The audit record for a partial withdrawal is unspecified. | Actor = the owner, reason `GOLDEN_REVOCATION`. A narrowing writes `CONSENT_REVOKED` with `removed_uses`. |
| N6 | Minor | §6 | Part D copies in `~/hl-spike-media/` are outside the system purge. | Add them to §6 and to the manual withdrawal checklist. |
| N7 | Minor | §8 | `processors[]` isn't defined for standing or derived versions. `OfflineCopy` has no consent-version link. The test count is inconsistent (15 vs 14). | Derived processors ⊆ the parent; add `consent_version` to `OfflineCopy`; use one test count. |

**Overengineering (reviewer's simplification):**
- **Drop `DEMO_GOLDEN`.** Build the golden project stock-voice only, or as just another rehearsal build. This removes the golden-revocation row, test 5, and the misclick risk (N9).
- **Drop the `DB_BACKUP` kind.** Keep the no-backup rule and the unregistered-file warning, and make the whole-`media/` hash scan a warning only.
- **One withdrawal path.** Any standing narrowing runs the cascade on failing scopes, plus `DELETION_PENDING` on the matching `OfflineCopy` kinds.

With these cuts the reviewer estimates about 2–3 days [reviewer ESTIMATE, not measured].

**Honesty:**
- "The §8 promise **becomes** something the code enforces" and Options row C "Yes, in code" overclaim, because nothing is built. Use "is designed to be enforced … for registered copies inside the system's media folder".
- The labels are otherwise correct.

**Demo and viva risks:**
- **N8:** only the owner can revoke (ADR 0011), so the speaker must be present and logged in for every revocation demo. Say so in ADR 0012, with the fallback of running the checkpoint tests on screen.
- **N9:** a misclick on revoke in the golden project removes D2 permanently. Fix with the `DEMO_GOLDEN` cut, or a confirmation dialog.
- "STANDARD consent outlives Part D?" Fixed by N3.
- "Removed D2 but the job kept saving?" Fixed by N2.

**Good:**
- The standing grant with narrower derived copies is a clean answer to ADR 0011.
- Rebuild-not-restore, with the manual restore named as a residual risk, matches ADR 0007.
- Withdrawal is final.

## Round 3: short final review (revision 3, 2026-10-06)

| | |
|---|---|
| **Reviewed** | Revision 3 of ADR 0020, and the N4 wording in `CONSENT_FORM.md` Part D |
| **Reviewer** | `critical-reviewer` agent (fresh context) |
| **Verdict** | **Approve with changes:** 0 blockers, 3 major, 4 minor. The reviewer says that after M1, M2 and M4 are fixed, the ADR is ready for the user's approval with a spot-check, not another full round. |
| **Status** | M7 (this status line) applied. **M1–M6 not applied; waiting for the user.** ADR 0020 stays Proposed. |

The assistant checked M3 against ADR 0003: its lock order ranks lock *types* (IdentityOwner → Job → artefacts → AuditChainHead), not several rows of the same type. Accurate.

**Round-2 fixes:**
- Fixed: N1, N2, N3, N5, N6, N7 and the simplification. The simplification has a gap (M4).
- Partly fixed: N4. The form's "real withdrawal" paragraph promises more than the ADR delivers (M2).

| # | Severity | Section | Problem | Proposed fix |
|---|---|---|---|---|
| M1 | **Major** | §1 gate, §5 step 2 | The gate re-checks the standing grant only for ACTIVE, expiry and Part D use. The subset rule (languages, processors) is checked only at creation, so narrowing languages or processors cascades nothing. | The gate also requires the scope's version to be ⊆ the **latest** standing version (uses, languages, processors, `expires_at`). Extend tests 8 and 11. |
| M2 | **Major** | Consent form "What counts as a real withdrawal" vs ADR §5 | The form says any revocation outside a rehearsal project is "a real withdrawal" (which §8 says deletes everything). In the ADR, revoking in a `STANDARD` project ends **that project only**; the standing grant, seed and recording stay. | Form: "Revoking inside a normal project ends that project's use only. To withdraw a Part D use or everything, untick it or press *Withdraw* on your consent page, or tell the §8 contact." Add the same hint to the `STANDARD` revoke dialog. |
| M3 | Minor (viva) | §3 lock line | ADR 0003 doesn't order several IdentityOwners. | "Several IdentityOwners are locked in ascending id order." |
| M4 | **Major** | §2 golden, §3 `--stock-only` | `--stock-only` claims to give "completed review, approval, export", but no step creates them. A scripted Approval invites "who approved this?" | (a) Build the golden project **once, by hand, through the real flow** with stock voices and real human review and approval; never reset it. Or (b) the seed stores stock audio, and the reset replays approval as `actor=system, replayed_from=<id>`, labelled "replayed". Make sure the rehearsal filter doesn't hide it. |
| M5 | Minor (viva) | §1 "Changing it means a new standing version" | Nothing stops the owner re-adding a use in the app without new paper evidence. | Any widening needs a new paper form ID as evidence; only narrowing can be done in the app alone. |
| M6 | Minor (consistency) | Consent form §6 Part D row, §8 item 2 | Both still say "demo reset snapshot", and §6 implies the golden project holds voice copies. | Say "demo seed copies", and "the golden project uses stock voices only". |
| M7 | Minor (honesty) | This file, round 2 status | Stale. | **Applied** (above). |

**Honesty:** no banned claims. The [ESTIMATE] label and "designed to be enforced … [CONFIRMED] only when tests 4–9 pass" are correct. The 2–3 day estimate is optimistic for 16 tests including concurrency tests. No one may sign Part D before both the form and ADR 0020 are approved.

**Biggest viva risk:** "Who approved the golden project?" (M4).
