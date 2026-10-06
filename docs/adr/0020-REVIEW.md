# Independent review: ADR 0020 (demo reset and identity withdrawal)

| | |
|---|---|
| **Reviewed** | `docs/adr/0020-demo-reset-and-identity-withdrawal.md` as of commit `5f16834` (Proposed) |
| **Reviewer** | `critical-reviewer` agent (fresh context), 2026-10-06, at the user's request |
| **Context read** | ADRs 0006, 0007, 0011, 0012, 0014; `CONSENT_FORM.md` (§6, §8, Part D); `CONSENT_FORM_REVIEW.md` round 2. The reviewer may have read the consent form before the round-2 P1–P8 edits landed; this doesn't change any finding. |
| **Verdict** | **Needs changes:** 2 blockers, 6 major, 6 minor |
| **Status** | **Not applied. ADR 0020 is unchanged and not approved.** Waiting for the user's decision. |

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
