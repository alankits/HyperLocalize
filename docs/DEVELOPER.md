# Developer guide

## Environment

- **Python:** 3.14 in `.venv`; `requirements.txt` (runtime), `requirements-dev.txt` (+ static ffmpeg), `requirements-ml.txt` (+ faster-whisper).
- **PostgreSQL 17** is required. The job queue uses `SKIP LOCKED`, and the audit table uses triggers.
  - Without Docker: `scripts/dev_postgres.sh start|stop|status` runs checksum-verified embedded binaries on a Unix socket in `~/.local/hl-dev/run`, port 5433.
  - With Docker: `docker-compose.yml`.
- **Settings** come from environment variables or `.env` (see `.env.example`):
  - `HYPERLOCALIZE_MODE` is `dev`, `test` or `demo`. **Mocks exist only in dev/test.** Demo mode requires `HL_SECRET_KEY`.
  - Media goes in `HL_MEDIA_ROOT`, outside the repo.

## Running

- **Web:** `manage.py runserver 127.0.0.1:8000`.
- **Workers:** `manage.py run_worker --lane default` and `--lane synthesis` (or `--lane all`). `--drain` runs until the queue is empty.
- **Tests:** `HYPERLOCALIZE_MODE=test manage.py test hyperlocalize`.
  - The optional real-model test needs `HL_TEST_WHISPER=1` and a downloaded model.
  - The optional MMS-TTS real-model test needs `HL_TEST_MMS=1` and `manage.py download_models --mms-tts`.
  - **Tests never call real Gemini** (ADR 0022): `manage.py test` forces test mode; Gemini is unavailable and `_post` refuses real HTTP unless `HL_TEST_GEMINI=1`. Use a fake transport (`opener=`) or patch `_post`.
  - `TransactionTestCase` subclasses must use `AuditSafeTransactionTestCase`: the audit trigger correctly blocks Django's TRUNCATE flush.
- **UML:** `python scripts/generate_uml.py` regenerates `docs/uml/class_diagram.md` from the models. Run it after every model change.

## Rules that keep the design honest

1. **Only `identity.services` decides consent, and only `audit.services.record()` writes audit records.** Call `record()` inside the action's transaction. Refusals use `record_standalone()`.
2. **Lock order** for every transaction that takes more than one lock: IdentityOwner (ascending id) → Localization → Scene → Job → artefacts → Export → AuditChainHead.
3. **Never update a translation, consent, render or audit row in place.** Insert a new version. Only the explicit status fields change.
4. **Any identity-using save** locks the owner and calls `locked_save_allowed(check, project, job)`.
5. **Audit details** hold identifiers and hashes only: no transcripts, translations, audio or names.
6. **No new consent rule** without an ADR.

## Adding a provider adapter

1. Subclass the interface in `pipeline/providers/base.py`: `TranscriptionProvider`, `TranslationProvider`, `MeaningCheckProvider` or `SpeechSynthesisProvider`.
2. Give it a unique `name`. Set `is_mock = True` only for mocks. Implement `available()`, which returns False if it isn't configured.
3. Decorate it with `@register`, and import the module in `base._load_adapters`.
4. **Raise errors that move the chain on:**
   - `QuotaExhausted`, `RateLimited` and `Unavailable` make the chain try the next adapter;
   - `ProviderOutputInvalid` does too, for malformed output.
5. **Data-use rules (ADR 0005/0021):** every localization and meaning-check adapter must declare `requires_hosted_llm_permission`: `True` for free-tier hosted LLMs, `False` for local models. An adapter that omits it is treated as hosted (fails closed), and a test checks that every registered adapter declares it.
6. **Local heavy models** run in the inference subprocess (`pipeline/inference.py`) so that the worker can kill them.
7. Add it to the chain in `DEFAULT_CHAINS`, or have an Administrator set it on the Policies page.
8. Add tests. Use a fake transport for remote APIs, as `GeminiAdapterTests` does.

## Adding a target language pack (critical-content checks)

Add a `TargetPack` to `localization/checks.py`, and target forms to `lexicons/units.json`. The forms come from a rater who reads the language, never from memory (ADR 0008). Until a pack exists, number checks report UNVERIFIABLE for that language.

## Commands

| Command | Purpose |
|---|---|
| `seed_demo` | Demo accounts and the demo scenario project |
| `run_worker` | Job worker, which also queues the periodic consent-expiry and retention sweeps |
| `verify_audit_chain` | Recompute the hash chain |
| `check_providers` | Adapters, media tools, usage, drift warnings |
| `build_demo_seed`, `demo_reset`, `register_offline_copy` | ADR 0020 demo mechanisms (Administrator only) |
