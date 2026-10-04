# ADR 0005: AI provider abstraction with clearly named mock providers

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7, CLAUDE.md §2 and §4

## Context

Each AI stage (transcription, translation, meaning-reversal flagging, speech synthesis, voice profiles) may change provider after the spike, or because of budget or data policy. Use case 8 (Administer Users, Providers and Policies) implies providers are configurable. Tests must run without paid APIs or network access. CLAUDE.md §2 requires mocks to be clearly named and listed as stubs.

**This ADR decides only the abstraction.** Which real providers to use is group B1, decided after the spike (`docs/SPIKE_PLAN.md`).

## Options Considered

| Criterion | Call provider SDKs directly | One interface per stage + adapters + mocks | Generic third-party abstraction library only |
|---|---|---|---|
| Swap providers | Hard | Easy | Depends on the library's coverage of audio/TTS |
| Testable offline | No | Yes | Partly |
| Enforces consent at the call site | No | Yes (signature requires a consent check, ADR 0006) | No |
| Explainability | High | High | Medium |

## Decision

- One interface per stage: `TranscriptionProvider`, `TranslationProvider`, `MeaningCheckProvider`, `SpeechSynthesisProvider`, `VoiceProfileProvider` (and later, if approved, `VisualContextProvider`).
- Identity-using methods (`SpeechSynthesisProvider` in cloned-voice mode, `VoiceProfileProvider.create`) **require a `ConsentCheck` object** issued by the consent gate as a parameter (ADR 0006).
- `VoiceProfileProvider` **must** implement `delete`. A provider without a deletion API is ineligible.
- Every result records: provider name, model identifier, model version (where the provider exposes one), prompt or template version, parameters, timestamps, and usage units (for cost measurement).
- Every interface has a `Mock…Provider` (e.g. `MockTranslationProvider`), marked in a code comment as a test stub and listed in `docs/STATUS.md` under stubs. Mocks are deterministic. Test-only barrier hooks support the mid-job revocation tests (ADR 0006).
- Real adapters can call third-party SDKs or third-party abstraction libraries internally. That is an implementation detail.
- Provider timeouts, retries and error types are normalised by the adapter, so the job layer handles one error model.

## Consequences

- **+** Spike results can be acted on by adding adapters, without redesign.
- **+** The full pipeline, including revocation, can be tested offline.
- **−** Some boilerplate per provider.
- **−** Provider-specific features (e.g. a vendor's own dubbing pipeline) can't be used as a black box, by design, because they would bypass the review and consent stages.
