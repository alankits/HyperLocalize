# Architecture Decision Records

Review of 0001–0008: `docs/ADR_REVIEW.md`. Provider facts and measurements: `docs/SPIKE_PLAN.md`. Licences and data terms: `docs/THIRD_PARTY_TERMS.md`.

## Group A: accepted 2026-10-05

| ADR | Title | Status |
|---|---|---|
| [0001](0001-modular-monolith.md) | Modular monolith (9 Django apps) with one worker process | **Accepted** (2026-10-05) |
| [0002](0002-postgresql-database.md) | PostgreSQL as the primary database | **Accepted** (2026-10-05) |
| [0003](0003-postgres-job-queue.md) | Hand-written Postgres job queue with explicit job states | **Accepted** (2026-10-05) |
| [0004](0004-media-storage-interface.md) | Media storage behind an interface, local filesystem for the MVP | **Accepted** (2026-10-05) |
| [0005](0005-provider-abstraction-and-mocks.md) | AI provider abstraction: free provider chains, mock providers, zero-spend policy | **Accepted** (2026-10-05) |
| [0006](0006-consent-gate-and-revocation.md) | Consent gate, checks at each stage boundary, revocation cascade | **Accepted** (2026-10-05) |
| [0007](0007-audit-records-hash-chain.md) | Append-only, hash-chained audit records | **Accepted** (2026-10-05) |
| [0008](0008-critical-information-verification.md) | Critical-information verification: rule-based hard checks + AI flags (Tamil-aware) | **Accepted** (2026-10-05) |
| [0009](0009-backend-django.md) | Backend framework: Django | **Accepted** (2026-10-05) |
| [0010](0010-frontend-server-rendered-htmx.md) | Frontend: server-rendered templates + HTMX | **Accepted** (2026-10-05) |
| [0011](0011-auth-and-project-roles.md) | Authentication and authorisation: sessions + project-scoped roles | **Accepted** (2026-10-05) |
| [0012](0012-deployment-and-demo-resilience.md) | Deployment: Docker Compose on a laptop, demo-resilience plan | **Accepted** (2026-10-05) |
| [0013](0013-use-case-boundaries.md) | Use-case boundaries and actor responsibilities (UML-ready) | **Accepted** (2026-10-05) |
| [0014](0014-core-data-model.md) | Core data model (UML-ready) | **Accepted** (2026-10-05) |

## Group B: waiting for spike results

| ADR | Title | Status |
|---|---|---|
| [0015](0015-identity-definition.md) | Identity definition: consent-governed voice identity with fallback | Pending spike results |
| [0016](0016-translation-method-and-provider.md) | Context-aware translation method and provider (English → Tamil) | Pending spike results |
| [0017](0017-transcription-provider.md) | Transcription (English ASR) provider | Pending spike results |
| [0018](0018-speech-synthesis-and-voice-provider.md) | Tamil speech synthesis: stock voice and cloned voice (open source) | Pending spike results |
| [0019](0019-kaggle-remote-gpu-batch.md) | Kaggle Notebooks as a remote GPU batch runtime | Pending spike results |

## Group C: proposed, waiting for approval

| ADR | Title | Status |
|---|---|---|
| [0020](0020-demo-reset-and-identity-withdrawal.md) | Demo reset by rebuild, offline-copy register, identity withdrawal (amends 0003, 0006, 0007, 0011, 0012, 0014) | **Accepted** (2026-10-06), revision 6 |

## Group D: accepted during the MVP build

| ADR | Title | Status |
|---|---|---|
| [0021](0021-published-public-content-and-mms-tts-stock-voice.md) | Published public content (Gemini allowed, provenance required) and MMS-TTS Tamil stock voice (amends 0005, 0014, 0016, 0018) | **Accepted** (2026-10-22), implemented |
| [0022](0022-quota-safe-batching-timing-fit-and-number-words.md) | Quota-safe batching with no silent MOCK, timing fit (1.2× cap, overrun check), Tamil track tags, number words, intelligibility proxy (amends 0005, 0008, 0016, 0021) | **Accepted** (2026-10-22), implemented |
