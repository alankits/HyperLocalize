# HyperLocalize — Implementation Status

**Current phase:** Phase 1: MVP build (authorized by the user 2026-10-06). **Application code exists** in `hyperlocalize/` (Django modular monolith). The throwaway spike tooling in `spike/` is separate.
**Branch:** `phase0/spike-scripts` (local only; **no GitHub remote is configured**). `master` holds the Phase 0 design (the repo has no `main` branch). The user said not to merge yet.
**Resume a session from:** this file → `docs/NEXT_STEPS.md` → `docs/adr/README.md`.
**Canonical product definition:** `docs/PRODUCT.md`. The health/ORS, English → Tamil material is the **spike and demo scenario**, not the product.
**How to run:** `README.md`. In short: `scripts/run_dev.sh`, then `python manage.py seed_demo`.

Labels: [IMPLEMENTED] = written **and** tested (tests listed); [PARTIAL]; [DESIGNED] = in an accepted ADR, not built; [BLOCKED]; [NOT MEASURED].

## Use cases

| # | Use case | Status | Notes |
|---|----------|--------|-------|
| 1 | Create and Generate a Localization Project | [IMPLEMENTED] | Create, configure audience and glossary, add members, start the pipeline. Tests: `tests/test_workflow.py`, `tests/test_views.py` |
| 2 | Upload and Analyze Source Video | [IMPLEMENTED] with MOCK or human transcript | ffprobe validation before acceptance, 5 min / 500 MB MVP limits, audio extraction, shot-cut detection, scenes and segments. **No real ASR model is integrated yet** (spike decides, ADR 0017): the transcript comes from a human-made SRT/VTT, or from `MockTranscriptionProvider` |
| 3 | Generate Context-Aware Localization Preview | [IMPLEMENTED] with MOCK; real candidate adapter [PARTIAL] | Context: neighbouring segments, speaker, audience profile, glossary, timing budget, reviewer instruction. **Visual context is not implemented.** The Gemini candidate adapter is written and tested against a fake HTTP layer only; **First live smoke test on 2026-10-12** (`docs/trials/2026-10-12-gemini-live-trial.md`; throwaway DB, demo text only). With `gemini-3.5-flash` (now the default; `gemini-2.5-flash` returns 404 for new keys), it localized 11/11 segments, and 3/11 meaning checks fell back to MOCK after HTTP 429 (per-minute cause [INFERRED]). **This is not a quality evaluation.** The free tier allows **20 requests per day per model [MEASURED]**, and one 11-segment run uses about 13. Fixed and tested on 2026-10-12: the 429 classification and retry, and the provider skip/fallback audit, including demo mode. Not yet re-verified live (quota used up). Rule checks (ADR 0008) and AI flags are implemented |
| 4 | Generate Localized Preview | [IMPLEMENTED] with MOCK voices | Backend-resolved rendering mode (CLONED / STOCK / SUBTITLES_ONLY), speech in a killable inference subprocess, bounded tempo, mixing, subtitles, scene preview MP4. **No real TTS or voice model yet** (ADR 0018): voices are MOCK tones |
| 5 | Review and Regenerate a Scene | [IMPLEMENTED] | Edits create HUMAN versions; override with a reason / acknowledge; accept; scene-only regeneration (script with an instruction, or preview) |
| 6 | Approve and Export Localization Package | [IMPLEMENTED] | Approval gate (all scenes accepted, no blocking checks, current previews, consent CP8, separation of duties). Export refused for MOCK output or invalid consent (CP9). Package: video, SRT, VTT, script, quality report, evidence manifest with the audit chain head |
| 7 | Revoke Consent and Stop Identity | [IMPLEMENTED] with MOCK voices | Standing and project consent, gate, locked saves, scope-only cascade, **mid-job kill tested**, purge, withdrawal, expiry sweep. ADR 0020 demo commands: see below |
| 8 | Administer Users, Providers and Policies | [IMPLEMENTED] | Policies and provider chains page. Users and memberships via Django admin (the seeded `admin` is staff and superuser). **Free-quota warnings (2026-10-12):** the Administrator enters each limit, with warnings at 80% and 100% on the page and in `check_providers`; tests: `tests/test_quota.py`. Only real localization and meaning-check adapters are metered; transcription and speech are not |
| 9 | Inspect Quality, Audit and Evidence | [IMPLEMENTED] | Audit trail filters, chain verification on demand, overrides list; `verify_audit_chain` command |

## Stubs / mocks (ADR 0005; never exportable)

| Mock | Where | What it does |
|---|---|---|
| `MockTranscriptionProvider` | `pipeline/providers/mock.py` | Placeholder "[MOCK] Transcript segment N." every 4 s |
| `MockTranslationProvider` | same | Copies the source, applies glossary target terms, prefix "[MOCK locale]" |
| `MockMeaningCheckProvider` | same | Flags source segments that contain a negation word (a keyword rule, not AI) |
| `MockStockVoiceProvider` | same | 440 Hz beeping tone, not speech |
| `MockClonedVoiceProvider` | same | 660 Hz beeping tone; imitates no one |

Mocks are registered only in `dev` / `test` mode; every output carries `is_mock`, the UI shows MOCK badges, and export is refused while any mock artefact is in the approved snapshot (tested).

## Tests

**MEASURED (2026-10-12):** 150 tests pass, 1 optional skipped (earlier counts: 102, 114, 126, 139) on PostgreSQL 17 (`HYPERLOCALIZE_MODE=test python manage.py test hyperlocalize`). Spike tooling: 75 pass, 1 skipped (separate suite in `spike/`).

**End-to-end over HTTP (MEASURED 2026-10-06):** `scripts/e2e_check.py` against a live dev server and worker: **15/15 steps passed**:
- consent, then a cloned-voice preview (MOCK);
- human review and approval;
- the MOCK export refused;
- revocation → preview 410, approval invalidated, stock fallback, reference clip deleted;
- a subtitles-only real export downloaded with its evidence manifest;
- the auditor verifying the chain.

**UML render check (2026-10-12):** all 10 Mermaid diagrams render with mermaid-cli 11.4.2: 8 in `docs/uml/README.md`, the class diagram, and the Phase 0 diagram. Semicolons in 9 sequence-diagram messages had broken one diagram; fixed.

**Screenshots (2026-10-12):** `docs/screenshots/`, eight pages (one per role) taken in headless Chromium from a throwaway seeded database. They show MOCK output.

## Known limitations (MVP build)

- **Open findings from the 2026-10-12 provider review (not fixed; waiting for user decisions):**
  - **Major: a meaning-check network call can run inside the consent lock.** `demo_reset` holds the IdentityOwner lock (`identity/demo.py:118`) while `save_translation` runs the Gemini meaning check per segment. A speaker's revocation can therefore wait for those calls. `edit_translation` also makes this call inside a web request.
  - **The quota ledger undercounts.** It counts only successful calls; retries and failed attempts that may use quota are not counted.
  - **Quota budget:** about 13 of the 20 daily requests per run. In demo mode, running out FAILS the localize job and leaves CHECK_UNAVAILABLE rows to acknowledge.
  - **Model alias:** only the alias (`gemini-3.5-flash`) is stored, not the model that answered.
  - **Transcription audit:** skips and fallbacks in the transcription stage are not audited (until ASR is integrated, ADR 0017).
  - **Quota windows:** `quota.py` has no per-minute window.
- **No real AI model has been run.** Every quality, speed or accuracy figure is NOT MEASURED.
- Docker is not installed on the laptop: `docker-compose.yml` and `Dockerfile` are **written but never run**. Development uses `scripts/dev_postgres.sh` (embedded PostgreSQL 17 binaries) and the `static-ffmpeg` package.
- The demo video is synthetic (test patterns and a tone). The demo script's health facts are [UNVERIFIED] (TEST_SCRIPT §4).
- Tamil number-word stems, unit forms and glossary forms are drafts or empty until a Tamil-literate rater fills them in, so many checks are UNVERIFIABLE by design (fail-safe).
- Retention sweeps (previews 30 days, exports 90 days; ADR 0004) are implemented and run hourly from `run_worker` (tested in `tests/test_views.py`). The source video is kept until the project is deleted.
- CP0 / CP3 (external ASR, Kaggle upload) have no code path yet, because no remote provider is integrated. The `external_transcription` consent use is therefore **not enforced by any gate** today.
- Independent code review of the consent and audit code: 1 blocker and 6 majors, **all fixed** (`docs/CODE_REVIEW.md`).

## Test material (2026-10-22)

- `test_datasets/`: 12 public English health-information videos (58–180 s; 22.4 min and 199 MB in total) from Wikimedia
  Commons, for drag-and-drop testing through the UI. Every file's SHA-1 matches Commons, all 12 pass
  `media_tools.validate_source`, and faster-whisper `small` found English speech in each. Five have human English
  subtitles (`.en.srt`) to use as reference transcripts. Details and attribution: `test_datasets/README.md`.
- **Not yet run through the app** (analysis → translation → render → export). Translation quality on them: [NOT MEASURED].
- The speakers have not consented to HyperLocalize: use `SUBTITLES_ONLY` / `STOCK_VOICE` only, never `CLONED_VOICE` (ADR 0006).
- They do not replace the scripted, consented spike clip (`SPIKE_PLAN.md` §2).

## Design documents

| Document | State |
|---|---|
| `docs/PHASE0_DISCOVERY.md` | Draft, revision 4. Where it differs from an ADR, the ADR takes precedence. |
| ADRs 0001–0014 | **Accepted** (2026-10-05) |
| ADRs 0015–0019 | **Pending spike results** |
| `docs/SPIKE_PLAN.md` | **Approved** 2026-10-05; **not run** (waiting on P3–P6, P8, P9). Round-2 fix P9 applied 2026-10-06: P6 lists permissions 3.0–3.6; M4 listeners rate both clones; rule 4 has an outcome for a skipped ECAPA run (Option A: listener control, A's clone ≥ 3 and B's clone ≤ 2). |
| `docs/THIRD_PARTY_TERMS.md` | Reference; checked 2026-10-05 |
| `docs/ADR_REVIEW.md` | Self-review and independent-review records (all findings resolved, 2026-10-05) |
| `docs/spike/CONSENT_FORM.md` | Draft v1 (spike prerequisite P6), waiting for approval. Not reviewed by a lawyer or ethics committee. Independent review applied (`docs/ADR_REVIEW.md`); preparation-review fixes applied 2026-10-05 (media path, spike log, 18+ confirmation, listener-name fields, stale labels). **Second independent review 2026-10-05: needs changes** (2 blockers, 6 major, 8 minor; `docs/spike/CONSENT_FORM_REVIEW.md`). **All 16 fixes approved and applied 2026-10-05.** New in the form: Appendix A (exact texts, initialled), signing only after the script freeze and at least 24 h after the explanation, faculty countersignature **required**. Team-specific blanks are still empty. Still a draft. **Round-2 review 2026-10-06: needs changes** (1 blocker: Part D says "approved by a human reviewer", but cloned previews come before review; 4 major, 4 minor; `CONSENT_FORM_REVIEW.md` round 2). **All fixes P1–P8 approved and applied 2026-10-06; N4 wording (D2 covers rehearsals; "real withdrawal" = outside a *Demo rehearsal* project) applied 2026-10-06, M2 and M6 wording applied 2026-10-06** (Part D now says AI drafts are unreviewed until checked; each D tick names the §5 limit it lifts; Part D copies, golden project and exports are covered in §6 and §8; "real withdrawal" is defined; backups line has a check field; English back-translation for Tamil items; signing waits for R2's check). Interim limit added to Part D. Still a draft; blanks still empty. |
| `docs/spike/TEST_SCRIPT.md` | Draft v1 (ORS health script, 27 segments, 256 words; length not yet timed). Health facts **[UNVERIFIED]** against the WHO source; waiting for approval. §7 reordered 2026-10-06 (P6): all of R1's Tamil texts, checked by R2, come before signing. |
| ADR 0020 (demo reset and identity withdrawal) | **Accepted** (2026-10-06, revision 6) under the user's rule "accept only if the final review has no blockers". The final review found blocker B1, which was fixed; the re-check found one bookkeeping blocker, which was fixed; the narrow diff check returned **BLOCKERS: none** (`0020-REVIEW.md` round 5). The amended ADRs carry precedence notes. **Designed, not implemented.** |
| `docs/PRODUCT.md` | **Canonical product definition** (2026-10-06): product vs MVP vs spike vs demo scenario vs implementation choices. Framing fixes applied to ADRs 0008, 0013, 0014 and 0015 and to Phase 0 §0 and §9 (wording only; no decision changed). |
| Interim rule (ADR 0012 note, SPIKE_PLAN §6) | **[CONFIRMED 2026-10-06]** No demo-reset snapshot or golden project may contain a real speaker's voice until ADR 0020 is approved. |
| `spike/` tooling | M1 scorer, M2 tally (blind MQM and pairwise sheets, agreement, chrF, rule 3), ADR 0008 hard checks, freeze, M3 seeded evaluation, M5 timing fit, M6 timing harness, rule 6. **75 unit tests pass and 1 is skipped (the optional sacreBLEU cross-check, which passes when sacreBLEU is installed); synthetic inputs only, 2026-10-05. Not run on real data.** Tamil lexicons are empty until R1/R2 fill them in. |
| `docs/EVALUATION.md` | Not created yet (created when the spike runs) |

## Spike readiness (2026-10-05)

| Item | State |
|---|---|
| P3 Hugging Face gated models | Requested; **pending**, not assumed |
| P4 Kaggle | Phone verified |
| P5 Gemini and Groq | Gemini key created (no billing) and in `.env` since 2026-10-12. It was pasted into a chat session, so rotate it before any real data is used. Groq ZDR enabled for inference APIs; whether it covers speech-to-text is [UNVERIFIED]. No audio to Groq yet. |
| P8 Demo laptop | i5-13450HX, 10 cores / 16 threads, 14 GiB RAM, kernel 7.0.0-34-generic. Ubuntu 26.04.1 LTS (read 2026-10-06). P8 done. |
| P9 Docker | Memory limit chosen: 8 GB (user, 2026-10-05). **Docker not installed yet. Blocks M6 and rule 6a.** |
| Media folder and spike log | Decided (user, 2026-10-05): `~/hl-spike-media/` and `~/hl-spike-media/spike-log.md` (append-only, timestamped, no raw content). Folder not created yet. |
| Consent form, script fact check, Tamil reference data, recording | **Not started** |

## Known issues

- No measured results of any kind yet; every number in the docs is a TARGET or an ESTIMATE.
- Q10–Q18 answered (defaults accepted 2026-10-05). Note: Q16 uses ADR 0004's 5 min / 500 MB, not the 3 min / 200 MB mentioned in chat.
- Q1 (official UML/problem statement) is still unanswered; the data model and use cases may need to change if UML arrives.
- **Design gap (found by the consent review, #2):** ADR 0012 §7's `demo_reset` snapshot holds the reference clip and cloned previews, outside the ADR 0006 purge. The consent form now promises that a withdrawal deletes the snapshot too, so ADR 0006/0012 must say how that happens before any system build. It needs an ADR change, which needs approval. Not urgent for the spike, which has no system. **Proposed fix: ADR 0020 (2026-10-06, Proposed, revision 4; spot-check says ready for approval).** Interim rule in force until then: no real voice in any snapshot or golden project. It also found that a whole-database restore would silently cut the ADR 0007 audit chain [INFERRED].
