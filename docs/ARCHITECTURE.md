# Architecture, modules and algorithms (as implemented)

Status labels: [IMPLEMENTED] = written and tested; [DESIGNED] = accepted ADR, not built; [NOT MEASURED] = no figure exists.

## 1. Shape

A **modular monolith** (ADR 0001):
- one Django codebase and one PostgreSQL database (ADRs 0002 and 0009);
- a **web process** that never blocks on long work;
- **worker processes** that claim jobs from a hand-written Postgres queue (ADR 0003): `run_worker --lane default|synthesis|all`.

Pages are server-rendered with htmx (ADR 0010). Media lives outside the web root behind a storage interface (ADR 0004). AI stages sit behind provider interfaces with an ordered chain per stage (ADR 0005). Deployment is planned as Docker Compose on one laptop (ADR 0012); the files are written but not yet run.

## 2. Modules (Django apps)

| App | Owns | Key code |
|---|---|---|
| `accounts` | User (`is_administrator`), ProjectMembership roles, Policy values, the rate-limited login | `permissions.py`: role checks used by every service |
| `projects` | Project, AudienceProfile, GlossaryTerm, Video, SpeakerTrack, media storage | `services.upload_video` (validates with ffprobe before accepting); `storage.LocalMediaStorage` |
| `localization` | Scene, Segment, Localization, SegmentTranslation (append-only versions), CheckResult | `services.localize_scene`, `checks.py` (ADR 0008) |
| `rendering` | SynthesisedSegment, RenderedScene | `services.render_scene` (mode resolution, CP4–CP7) |
| `review` | Review, RegenerationRequest, Approval | `services.approve` (the gate), `request_changes` |
| `identity` | IdentityOwner, Consent (standing / project), VoiceProfile, OfflineCopy | `services.evaluate` (**the only consent decider**), `demo.py` (ADR 0020) |
| `exports` | Export | `services.request_export`, `build_export` |
| `audit` | AuditRecord, AuditChainHead | `services.record` (**the only writer**), `verify_chain` |
| `pipeline` | Job, ProviderConfig, ProviderUsage | `jobs.py`, `handlers.py`, `inference.py`, `providers/` |

The apps call each other only through `services.py` functions, and no signals are used (ADR 0001).

## 3. Algorithms

**Scene planning** (`localization.services.plan_scenes`) [IMPLEMENTED]:
- Segments come from the transcript.
- A scene boundary is placed between two segments when any of these holds:
  - a **shot cut**, found by ffmpeg's scene-change score, falls in the gap;
  - the pause is at least 1.5 s;
  - the scene would grow longer than 30 s.
- A boundary sits at the cut, or else at the middle of the pause.
- Scenes are contiguous and cover the whole video.
- The thresholds are an implementation choice and have not been tuned.

**Context-aware localization** (`localization.services.build_request`) [IMPLEMENTED, method PROPOSED]:
- Each segment is sent with its context: 2 neighbouring segments on each side, the speaker, the audience profile (locale, formality, reading level, cultural notes, declared unit conversions), the glossary, its timing budget, and any reviewer instruction.
- Every saved draft records which context inputs were used, plus the adapter, model and prompt version.
- **Visual context is not used.**
- A context-free fallback records no context inputs.

**Critical-content checks** (`localization/checks.py`, ADR 0008) [IMPLEMENTED]:
- **Language-neutral framework:** a source-language number reader (English: digits, groupings, times, number words, "once/twice") plus a target **language pack** (Tamil: Tamil digits; number-word stems and non-positional numerals make a result UNVERIFIABLE).
- **Numbers** are compared as multisets.
- **Units** come from a lexicon with forms per language. A declared conversion makes the result UNVERIFIABLE, as a fail-safe.
- **Glossary** forms are matched by prefix, so inflected forms still match. A term with no target forms gives UNVERIFIABLE, never PASS.
- **Structural checks:** empty, untranslated, mostly Latin script for a non-Latin target, and over the timing budget.
- **Effect:** FAIL or UNVERIFIABLE blocks approval until the text is fixed or a reviewer overrides it with a written reason.
- **AI flags** (`MeaningCheckProvider`) need an acknowledgement, and are never called verification.

**Consent gate** (`identity.services.evaluate`, ADRs 0006 and 0020) [IMPLEMENTED]: identity use is allowed only if all of these hold:
- the owner has not withdrawn;
- the latest project consent is ACTIVE, unexpired, and includes the use and the language;
- it has a parent standing consent;
- the latest standing consent is ACTIVE, unexpired, and permits the project's purpose (a rehearsal needs both STANDARD and DEMO_REHEARSAL);
- the project consent is still within the standing consent;
- the job is not flagged for cancellation.

Saves (CP5, CP7, CP9) lock the IdentityOwner row and run the gate again before writing.

**Revocation cascade** (`identity.services._cascade`) [IMPLEMENTED]. It runs only when identity use actually ended, and covers only this owner's artefacts in this project. In one transaction:
- scenes are set to NEEDS_REGENERATION;
- render jobs are cancelled;
- artefacts are quarantined;
- the reference clips are marked DELETED;
- only the approvals and exports that contain this owner's identity are invalidated or blocked;
- a purge is queued.

After commit, stock-voice fallback renders are queued, and they must be reviewed again.

**Lock order** (every multi-lock transaction): IdentityOwner (ascending id) → Localization → Scene → Job → artefacts → Export → AuditChainHead.

**Mid-job stop** [IMPLEMENTED; stop time NOT MEASURED, a test bound of < 8 s passes]:
- Speech runs in an **inference subprocess**.
- While waiting, the worker polls the job's cancel flag and the consent gate about once a second, and **kills** the subprocess on cancel.

**Rendering mode** (`rendering.services.resolve_mode`, ADR 0015), resolved per speaker:
- SUBTITLES_ONLY, if policy forbids synthesis;
- otherwise CLONED_VOICE, only with valid consent, an active reference clip, cloning allowed by policy, and an available cloning adapter;
- otherwise STOCK_VOICE.

The note giving the reason is shown to the reviewer.

**Timing fit:** if the synthesised audio is longer than its slot, the tempo is raised, at most to 1.15×. 15 % is an assumed working threshold (SPIKE_PLAN M5).

**Audit hash chain** (ADR 0007) [IMPLEMENTED]:
- `hash = SHA-256(prev_hash + canonical_json(record))`;
- appends are serialised by locking a single head row, always last;
- PostgreSQL triggers reject UPDATE, DELETE and TRUNCATE;
- `verify_audit_chain` recomputes the whole chain;
- each export manifest carries the chain head.

This is **tamper-evident, not tamper-proof**: someone with database access could rebuild the whole chain.

**Approval gate** (`review.services.approve`). Approval is refused unless all of these hold:
- every scene is accepted;
- no blocking checks remain on the latest versions;
- every preview is current;
- CP8 consent passes;
- separation of duties: the approver did not edit any segment in this version.

On approval, an immutable snapshot of the exact versions is frozen, and any later change invalidates it.

**Export gate** (`exports.services`). Export is refused if the approval is invalid, if **any artefact in the snapshot is MOCK** (a hard rule), if any artefact is quarantined, or if CP9 consent fails. The package contains:
- the localized MP4 (original picture; original audio ducked under the speech; soft subtitles);
- SRT and VTT subtitles;
- `script.json`;
- `quality_report.json`;
- `evidence_manifest.json`, with hashes, providers, rendering modes, consent versions, reviews and the chain head. Its format is [PROPOSED].

## 4. Demo mechanisms (ADR 0020) [IMPLEMENTED, partly]

- `build_demo_seed` registers the owner's reference clip in `media/offline/`.
- `demo_reset` builds a **new** DEMO_REHEARSAL project from the source project's valid approval. Its derived consent is never wider than the parent and never remote. It only appends audit records.
- `register_offline_copy` registers a screen recording.
- `check_providers` reports the provider chains and media tools, and gives drift warnings.

Importing pre-rendered cloned audio into the seed is **not implemented**.

## 5. Not implemented (honest list)

- Real TTS and voice-cloning models.
- Real ASR on speech: the faster-whisper candidate is wired up, but has only been run on non-speech audio.
- Live Gemini calls (tested only against a fake HTTP layer).
- Visual context.
- Remote runtimes (Kaggle), external ASR (CP0), and CP3.
- Usage metering for transcription and speech (only real localization and meaning-check adapters write the usage ledger; quota warnings cover those).
- C2PA.
- Lip-sync and face processing (out of scope).
