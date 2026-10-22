# HyperLocalize

**A context-aware, identity-preserving video localization system.** It is a controlled workflow that adapts source video for a target audience. AI output is only a draft: a human reviews every scene, problem scenes can be regenerated one at a time, an approval gate comes before export, a speaker's identity is used only while their consent is valid, and every step is recorded in a tamper-evident audit trail.

> The canonical product definition is [`docs/PRODUCT.md`](docs/PRODUCT.md). The current demo scenario (English health information about ORS, localized into Tamil) is a **test case**, not the product's domain.

**Honest status:** the full workflow runs end to end and is tested. The AI stages run on **clearly labelled MOCK providers**, a human-made transcript, and human edits. Real models are added after the spike (`docs/SPIKE_PLAN.md`). Candidate adapters exist for faster-whisper (local transcription) and Gemini (translation). See [`docs/STATUS.md`](docs/STATUS.md). No quality or speed figure has been measured.

## Quick start (Linux laptop, no Docker, no sudo)

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt   # Django, psycopg, static ffmpeg
cp .env.example .env                                                     # optional: edit values
scripts/run_dev.sh            # dev PostgreSQL 17, migrations, a worker, and the web server on 127.0.0.1:8000
# in a second terminal:
.venv/bin/python manage.py seed_demo --password 'choose-a-password'
```

Then open http://127.0.0.1:8000 and sign in as one of these demo accounts:

| Account | Role |
|---|---|
| `manager` | Localization Manager |
| `manager2` | Second Localization Manager (separation of duties) |
| `reviewer` | Reviewer / Linguist |
| `operator` | Media Operator |
| `auditor` | Auditor / Faculty Evaluator |
| `speaker` | Speaker / Identity Owner |
| `admin` | Administrator |

The demo walk-through is in [`docs/USER_MANUAL.md`](docs/USER_MANUAL.md).

**With Docker** (written but **not yet run**, because Docker is not installed on the development laptop): `docker compose up --build`, then `docker compose exec web python manage.py migrate`.

**Optional real candidates:**
- `pip install -r requirements-ml.txt` adds faster-whisper. It is used only after the model has been downloaded.
- **Tamil stock voice (MMS-TTS, ADR 0021):** `pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1`, then `pip install -r requirements-ml.txt`, then `python manage.py download_models --mms-tts` (about 280 MB, CC-BY-NC-4.0: non-commercial). Restart the worker afterwards.
- **Published public content (ADR 0021):** choose it when creating a project for a published video whose licence permits reuse, and record the source URL and licence. Gemini can then translate it; the provenance goes into the export evidence.
- `HL_GEMINI_API_KEY` in `.env` enables Gemini on free-tier, scripted-content projects only.

## Tests

```bash
HYPERLOCALIZE_MODE=test .venv/bin/python manage.py test hyperlocalize
```

Last run (2026-10-12): 139 passed, 1 optional skipped.

## Repository map

| Path | What |
|---|---|
| `hyperlocalize/` | The Django modular monolith. One app per concern: accounts, projects, localization, rendering, review, identity, exports, audit, pipeline |
| `docs/PRODUCT.md` | Product definition |
| `docs/STATUS.md` | Honest status per use case |
| `docs/adr/` | Accepted decisions |
| `docs/ARCHITECTURE.md` | Architecture, modules and algorithms |
| `docs/uml/` | UML; the class diagram is generated from the code |
| `docs/USER_MANUAL.md`, `docs/DEVELOPER.md` | How to use and how to extend |
| `docs/TESTING.md`, `docs/EVALUATION.md` | Tests run; metrics (TARGET vs MEASURED) |
| `docs/VIVA.md` | Defending the project |
| `spike/` | Throwaway spike tooling (separate test suite) |

## What it is not

- It is not a health, ORS or Tamil-only app.
- It is not a voice-cloning product.
- It is not an autonomous dubbing pipeline.
- It does no lip-sync or face processing.
- It is not production-ready, and no security or compliance claim is made.
