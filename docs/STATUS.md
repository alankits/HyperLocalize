# HyperLocalize — Implementation Status

**Current phase:** Phase 0: Discovery and Design. **No application code exists.**
**Branch:** `phase0/discovery-report` (not merged to `master`).
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
| ADRs 0001–0014 | **Proposed**, waiting for approval |
| ADRs 0015–0019 | **Pending spike results** |
| `docs/SPIKE_PLAN.md` | Plan only, **not run**, waiting for approval |
| `docs/THIRD_PARTY_TERMS.md` | Reference; checked 2026-10-05 |
| `docs/ADR_REVIEW.md` | Self-review and independent-review records (all findings resolved, 2026-10-05) |
| `docs/spike/CONSENT_FORM.md` | Draft v1 (spike prerequisite P6), waiting for approval. Not reviewed by a lawyer or ethics committee. Independent review applied (`docs/ADR_REVIEW.md`). |
| `docs/spike/TEST_SCRIPT.md` | Draft v1 (ORS health script, 27 segments, 256 words; length not yet timed). Health facts **[UNVERIFIED]** against the WHO source; waiting for approval. |
| `docs/EVALUATION.md` | Not created yet (created when the spike runs) |

## Known issues

- No measured results of any kind yet; every number in the docs is a TARGET or an ESTIMATE.
- Open questions Q10–Q18 use the marked proposed defaults in the ADRs.
- The `critical-reviewer` agent type loads only in a new session; this session's independent review used a built-in read-only agent with the same brief.
