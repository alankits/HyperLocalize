# HyperLocalize — Implementation Status

**Current phase:** Phase 0: Discovery and Design. **No application code exists.** Throwaway spike tooling exists in `spike/` (not part of the app).
**Branch:** `master` holds the Phase 0 design (merged 2026-10-05). The spike tooling is on `phase0/spike-scripts` and is **not merged**: the user said not to merge yet (2026-10-05).
**Resume a session from:** this file → `docs/NEXT_STEPS.md` → `docs/adr/README.md`.

Status values: Implemented (tested) / Partial / Stubbed / Not started.

| # | Use case | Status |
|---|----------|--------|
| 1 | Create and Generate a Localization Project | Not started |
| 2 | Upload and Analyze Source Video | Not started |
| 3 | Generate Context-Aware Localization Preview | Not started |
| 4 | Generate Localized Preview | Not started |
| 5 | Review and Regenerate a Scene | Not started |
| 6 | Approve and Export Localization Package | Not started |
| 7 | Revoke Consent and Stop Identity | Not started |
| 8 | Administer Users, Providers and Policies | Not started |
| 9 | Inspect Quality, Audit and Evidence | Not started |

## Stubs / mocks

None yet. Planned mocks (ADR 0005) will be listed here when written.

## Design documents

| Document | State |
|---|---|
| `docs/PHASE0_DISCOVERY.md` | Draft, revision 4. Where it differs from an ADR, the ADR takes precedence. |
| ADRs 0001–0014 | **Accepted** (2026-10-05); 0006, 0007, 0011, 0012 and 0014 amended by ADR 0020 (2026-10-06) |
| ADRs 0015–0019 | **Pending spike results** |
| `docs/SPIKE_PLAN.md` | **Approved** 2026-10-05; **not run** (waiting on P3–P6, P8, P9). Round-2 fix P9 applied 2026-10-06: P6 lists permissions 3.0–3.6; M4 listeners rate both clones; rule 4 has an outcome for a skipped ECAPA run (Option A: listener control, A's clone ≥ 3 and B's clone ≤ 2). |
| `docs/THIRD_PARTY_TERMS.md` | Reference; checked 2026-10-05 |
| `docs/ADR_REVIEW.md` | Self-review and independent-review records (all findings resolved, 2026-10-05) |
| `docs/spike/CONSENT_FORM.md` | Draft v1 (spike prerequisite P6), waiting for approval. Not reviewed by a lawyer or ethics committee. Independent review applied (`docs/ADR_REVIEW.md`); preparation-review fixes applied 2026-10-05 (media path, spike log, 18+ confirmation, listener-name fields, stale labels). **Second independent review 2026-10-05: needs changes** (2 blockers, 6 major, 8 minor; `docs/spike/CONSENT_FORM_REVIEW.md`). **All 16 fixes approved and applied 2026-10-05.** New in the form: Appendix A (exact texts, initialled), signing only after the script freeze and at least 24 h after the explanation, faculty countersignature **required**. Team-specific blanks are still empty. Still a draft. **Round-2 review 2026-10-06: needs changes** (1 blocker: Part D says "approved by a human reviewer", but cloned previews come before review; 4 major, 4 minor; `CONSENT_FORM_REVIEW.md` round 2). **All fixes P1–P8 approved and applied 2026-10-06; N4 wording (D2 covers rehearsals; "real withdrawal" = outside a *Demo rehearsal* project) applied 2026-10-06, M2 and M6 wording applied 2026-10-06** (Part D now says AI drafts are unreviewed until checked; each D tick names the §5 limit it lifts; Part D copies, golden project and exports are covered in §6 and §8; "real withdrawal" is defined; backups line has a check field; English back-translation for Tamil items; signing waits for R2's check). The interim limit added to Part D was superseded by ADR 0020 the same day. Still a draft; blanks still empty. |
| `docs/spike/TEST_SCRIPT.md` | Draft v1 (ORS health script, 27 segments, 256 words; length not yet timed). Health facts **[UNVERIFIED]** against the WHO source; waiting for approval. §7 reordered 2026-10-06 (P6): all of R1's Tamil texts, checked by R2, come before signing. |
| ADR 0020 (demo reset and identity withdrawal) | **Accepted** (user, 2026-10-06), revision 4, after 3 review rounds and a spot-check (`docs/adr/0020-REVIEW.md`). **Amendments applied** to ADRs 0006 (gate, locked saves, scope-only cascade, purge, expiry, narrowing), 0007 (new audit actions), 0011 (owner's standing grant; the Administrator only derives or records), 0012 (items 1, 2, 3, 7, new item 11; interim rule superseded) and 0014 (new fields, `OfflineCopy`, invariants 6 and 8). Design only: nothing built or tested. |
| Interim rule (2026-10-06) | **Superseded** by ADR 0020 (accepted 2026-10-06). The golden project is permanently stock-voice only; a demo seed may hold a real voice only with Part D D1 and D2. |
| `spike/` tooling | M1 scorer, M2 tally (blind MQM and pairwise sheets, agreement, chrF, rule 3), ADR 0008 hard checks, freeze, M3 seeded evaluation, M5 timing fit, M6 timing harness, rule 6. **75 unit tests pass and 1 is skipped (the optional sacreBLEU cross-check, which passes when sacreBLEU is installed); synthetic inputs only, 2026-10-05. Not run on real data.** Tamil lexicons are empty until R1/R2 fill them in. |
| `docs/EVALUATION.md` | Not created yet (created when the spike runs) |

## Spike readiness (2026-10-05)

| Item | State |
|---|---|
| P3 Hugging Face gated models | Requested; **pending**, not assumed |
| P4 Kaggle | Phone verified |
| P5 Gemini and Groq | Gemini key created (no billing; not yet in `.env`). Groq ZDR enabled for inference APIs; whether it covers speech-to-text is [UNVERIFIED]. No audio to Groq yet. |
| P8 Demo laptop | i5-13450HX, 10 cores / 16 threads, 14 GiB RAM, kernel 7.0.0-34-generic. Ubuntu 26.04.1 LTS (read 2026-10-06). P8 done. |
| P9 Docker | Memory limit chosen: 8 GB (user, 2026-10-05). **Docker not installed yet. Blocks M6 and rule 6a.** |
| Media folder and spike log | Decided (user, 2026-10-05): `~/hl-spike-media/` and `~/hl-spike-media/spike-log.md` (append-only, timestamped, no raw content). Folder not created yet. |
| Consent form, script fact check, Tamil reference data, recording | **Not started** |

## Known issues

- No measured results of any kind yet; every number in the docs is a TARGET or an ESTIMATE.
- Q10–Q18 answered (defaults accepted 2026-10-05). Note: Q16 uses ADR 0004's 5 min / 500 MB, not the 3 min / 200 MB mentioned in chat.
- Q1 (official UML/problem statement) is still unanswered; the data model and use cases may need to change if UML arrives.
- **Design gap (found by the consent review, #2):** ADR 0012 §7's `demo_reset` snapshot holds the reference clip and cloned previews, outside the ADR 0006 purge. The consent form now promises that a withdrawal deletes the snapshot too, so ADR 0006/0012 must say how that happens before any system build. It needs an ADR change, which needs approval. Not urgent for the spike, which has no system. **Resolved by ADR 0020 (accepted 2026-10-06).** Interim rule in force until then: no real voice in any snapshot or golden project. It also found that a whole-database restore would silently cut the ADR 0007 audit chain [INFERRED].

- **UML diagrams to update (from ADR 0020):** class diagram (`OfflineCopy`; Project.purpose; Consent kind, parent and part_d_uses; IdentityOwner withdrawal fields; Export `PURGED`), Consent state diagram (standing and project versions, narrowing, withdrawal), UC7 activity or sequence diagram (narrowing and withdrawal paths). No UML exists yet (Q1).
