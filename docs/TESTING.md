# Testing

**MEASURED (2026-10-06):** `HYPERLOCALIZE_MODE=test manage.py test hyperlocalize` gives **126 tests passed, 1 skipped** (an optional real-model test, which passes with `HL_TEST_WHISPER=1`). The run uses real PostgreSQL 17, real ffmpeg, MOCK AI providers and synthetic media. The spike tooling has its own suite: `cd spike && python3 -m unittest`, giving 75 passed and 1 skipped.

| Area | File | What is proven |
|---|---|---|
| Audit chain | `audit/tests.py` | Chain links and verifies. UPDATE, DELETE and TRUNCATE are rejected by the database. Tampering with the trigger disabled is detected. No floats or raw content are stored. A record must be written inside a transaction |
| Consent gate (negatives first) | `identity/tests.py` | No consent, no standing consent, Administrator or other-user grants, wider-than-standing, wrong use or language, revoked, expired, an old version after revocation, narrowing cascades, withdrawal is final, widening needs a new form, the expiry sweep |
| Workflow | `tests/test_workflow.py` | Analysis into scenes at the shot cut; context inputs recorded; previews rendered; invalid upload and wrong-role rejection; mock output fails rule checks; scene accept is blocked by open checks; overrides need a reason and the reviewer role; a number mismatch blocks; AI flags need acknowledgement; scene-only regeneration; the approval gate; separation of duties; **mock output is never exportable**; a full human-only export; an edit after approval invalidates it |
| Identity in the workflow | `tests/test_identity_workflow.py` | Cloned mode with consent; stock fallback without it; a voice profile needs consent; the revocation cascade quarantines, purges and falls back; scope isolation; **a real mid-job kill of the inference subprocess** |
| Code-review regressions | `tests/test_review_fixes.py` | The grant path cannot narrow; the purge is never cancelled; reference clips are decided at revocation; harmless narrowing keeps work valid; expiry re-checked under the lock; revocation leaves other exports alone; demo reset links only the owner's speaker; **a two-owner mid-job stop**; **withdraw vs reset in both orders** |
| Demo reset | `tests/test_demo_reset.py` | Administrator only; rebuild only appends; refusals for purposes, drift and withdrawal; a rehearsal revocation leaves the source and seed alone; offline-copy permission; drift warning |
| Web layer | `tests/test_views.py` | Pages render per role; 403 for outsiders; wrong-role POSTs refused; previews only for members; **CP10 returns 410 after revocation**; the identity owner has no project access; admin-only policies; login rate limit; periodic sweeps; retention |
| Providers | `pipeline/tests.py` | Mocks are absent in demo mode; chain fallback and Administrator order; data-use rule; Gemini parsing, quota handling and key-in-header against a **fake** HTTP layer; transcript parsing; job cancel and retry |
| Checks | `localization/tests.py` | Numbers (digits, words, Tamil digits, Indian grouping, the fail-safe for number words, an unknown language pair); units; conversions; glossary; structure; scene planning |

**Not tested:**
- any real AI model on real data;
- the Docker images;
- a browser (only the Django test client and curl);
- performance and load.
