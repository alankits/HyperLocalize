# HyperLocalize — Implementation Status

**Current phase:** Phase 0: Discovery and Design. **No application code exists.** Throwaway spike tooling exists in `spike/` (not part of the app).
**Branch:** `master` (Phase 0 design merged 2026-10-05).
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
| ADRs 0001–0014 | **Accepted** (2026-10-05) |
| ADRs 0015–0019 | **Pending spike results** |
| `docs/SPIKE_PLAN.md` | **Approved** 2026-10-05; **not run** (waiting on P3–P6, P8) |
| `docs/THIRD_PARTY_TERMS.md` | Reference; checked 2026-10-05 |
| `docs/ADR_REVIEW.md` | Self-review and independent-review records (all findings resolved, 2026-10-05) |
| `docs/spike/CONSENT_FORM.md` | Draft v1 (spike prerequisite P6), waiting for approval. Not reviewed by a lawyer or ethics committee. Independent review applied (`docs/ADR_REVIEW.md`). |
| `docs/spike/TEST_SCRIPT.md` | Draft v1 (ORS health script, 27 segments, 256 words; length not yet timed). Health facts **[UNVERIFIED]** against the WHO source; waiting for approval. |
| `spike/` tooling | M1 scorer, ADR 0008 hard checks, freeze, M3 seeded evaluation, M5 timing fit, M6 timing harness, rule 6. **51 unit tests pass (synthetic inputs only, 2026-10-05). Not run on real data.** Tamil lexicons are empty until R1/R2 fill them in. |
| `docs/EVALUATION.md` | Not created yet (created when the spike runs) |

## Known issues

- No measured results of any kind yet; every number in the docs is a TARGET or an ESTIMATE.
- Q10–Q18 answered (defaults accepted 2026-10-05). Note: Q16 uses ADR 0004's 5 min / 500 MB, not the 3 min / 200 MB mentioned in chat.
- Q1 (official UML/problem statement) is still unanswered; the data model and use cases may need to change if UML arrives.
- The `critical-reviewer` agent type loads only in a new session; this session's independent review used a built-in read-only agent with the same brief.
