# ADR 0005: AI provider abstraction: free provider chains, mock providers, zero-spend policy

> **Amended by ADR 0022 (2026-10-22):** after a real provider *fails*, a MOCK never takes its place (pending + retry; meaning check CHECK_UNAVAILABLE). Gemini is disabled in test mode. ADR 0022 takes precedence where they differ.

> **Amended by ADR 0021 (2026-10-22):** the data-use rule also allows a free-tier hosted LLM for `PUBLISHED_PUBLIC` projects whose source URL and licence are recorded. ADR 0021 takes precedence where they differ.

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-04; revised 2026-10-05: ADR review, zero-budget Q4, independent review.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7, CLAUDE.md §2 and §4, `docs/THIRD_PARTY_TERMS.md`

## Context

Q4 (revised): **zero budget** for AI services and infrastructure. Free tiers and open-source models only. No local GPU; Kaggle Notebooks (free, about 30 GPU hours/week) may run GPU-heavy steps. Requirements from that answer:
1. Every AI provider must have a **free alternative plus a clearly named mock**, so that a change in free-tier quota can't block development or the demo.
2. The terms must be documented: free-tier Gemini may use submitted data for training, and IndicF5 is treated as non-commercial (`docs/THIRD_PARTY_TERMS.md`).

Free tiers change without notice and have rate limits. Local open-source models run on a CPU-only laptop, so they may be slow. CLAUDE.md §2 forbids presenting mocks as real.

**This ADR decides the abstraction, the fallback mechanism and the spending policy.** Which provider is primary is decided by ADRs 0015–0019 after the spike.

## Options Considered

| Criterion | One provider per stage | **Ordered provider chain per stage (free primary → free alternative), mock only outside the demo chain** | Mocks as an automatic last resort in the live chain |
|---|---|---|---|
| Survives a free-tier quota change | No | **Yes** | Yes |
| Honesty (CLAUDE.md §2) | Yes | **Yes: every fallback is recorded and shown** | **No: a mock could silently reach a preview** |
| Complexity | Low | Medium (one small chain class) | Medium |
| Viva | Fragile | **"Each stage has a free plan B, and we show which one ran"** | Indefensible |

## Decision

**Interfaces** are unchanged in shape: `TranscriptionProvider`, `TranslationProvider`, `MeaningCheckProvider`, `SpeechSynthesisProvider`, `VoiceProfileProvider`. Identity-using methods require a `ConsentCheck` (ADR 0006).

**Provider chain per stage.** Each stage is configured (by the Administrator, UC8) as an ordered list of adapters. When an adapter raises `QuotaExhausted`, `RateLimited` (after retries) or `Unavailable`, the next adapter is tried. The adapter that actually ran is recorded on the output and **shown to the reviewer** (e.g. "translated by fallback: IndicTrans2, no context, no rationale").

| Stage | Free primary (provisional; spike decides) | Free alternative | Mock |
|---|---|---|---|
| Transcription (English) | **faster-whisper on local CPU** (MIT). Source audio stays on the laptop. | Groq `whisper-large-v3` (free plan), **only** if the project's `allow_external_audio` is on and consent checkpoint CP0 passes (ADR 0006) | `MockTranscriptionProvider` |
| Translation (context-aware) | Gemini Flash (**free tier**), only when `Project.data_classification = SCRIPTED_TEAM` | One Groq-hosted open LLM (free plan; production model only) → last resort **IndicTrans2 on local CPU** (context-free, marked) | `MockTranslationProvider` |
| Meaning-check (AI flags) | An LLM, same or different family to the translator (decided by spike rule 7) | The other one. If both are unavailable, every segment gets a **`CHECK_UNAVAILABLE`** flag that needs manual acknowledgement (fail-safe). | `MockMeaningCheckProvider` |
| Stock Tamil voice | MMS-TTS Tamil or Indic Parler-TTS (**local CPU**) | The other local model *(ElevenLabs dropped after review: two local voices already exist, and it would add a hosted dependency with attribution terms)* | `MockSpeechSynthesisProvider` |
| Cloned Tamil voice | **IndicF5 on Kaggle GPU** (batch, ADR 0019) or **IndicF5 on local CPU** (spike decides which is primary) | The other IndicF5 runtime. If both are unavailable, the **rendering mode falls back to `STOCK_VOICE`** (ADR 0015); no other free Tamil cloning model is in scope. | `MockSpeechSynthesisProvider`, `MockVoiceProfileProvider` |

There is honestly **no second independent free Tamil cloning model** in this plan. For cloning, the "free alternative" is a second *runtime* of the same model, plus the governed stock-voice fallback.

**Mocks are never in a live chain.**
- Mock adapters are only registered when `HYPERLOCALIZE_MODE=test` or `dev`.
- Mock audio is an obvious tone, mock text is prefixed `[MOCK]`, and the UI shows a **"MOCK OUTPUT"** badge.
- **Export is refused if any artefact in the snapshot came from a mock.** This is a hard rule with a test.
- Mocks are marked in code comments and listed under stubs in `docs/STATUS.md`.

**Zero-spend policy (replaces the ₹ budget cap).**
- No adapter may be configured with a billing-enabled account.
- Providers that need a payment method even for their free tier are **ineligible** (e.g. Google Cloud TTS and Translation; see `THIRD_PARTY_TERMS.md` §3).
- The `ProviderUsage` ledger now tracks **free-quota consumption** (requests, tokens, audio seconds, Kaggle GPU hours). It warns the Administrator at 80% of each known daily or weekly limit, so the team can switch to the alternative *before* a demo, not during it.

**Data-use rule for free tiers.** This is **enforced in code**, not just stated as a policy:
- **Gemini free tier:** the chain **skips Gemini** unless `Project.data_classification = SCRIPTED_TEAM` (set by the Manager, who attests that the content is team-authored and scripted). Only text is sent, never audio. Each skip is audited, and there is a test. Note: segment text comes from ASR, so it can include ad-libs. The attestation covers the recording session, not just the script.
- **Voice data:** reference clips and cloned speech go only to local models or Kaggle private datasets (with `remote_voice_processing` consent). Source audio goes to Groq **only** with `external_transcription` consent (CP0). By default, all audio stays on the laptop.

The processors used are recorded in the Consent and in the evidence manifest.

**Local model runtime.** Local models (faster-whisper, IndicTrans2, MMS-TTS, Indic Parler-TTS, IndicF5 on CPU) run in a **separate inference subprocess** owned by the worker. **One model is loaded at a time** *(added after review, because of laptop RAM)*: switching model type unloads the previous one. The worker can **kill** the subprocess to cancel immediately (ADR 0006) and restarts it on the next call.

**Recorded on every call:** adapter, model identifier and version, prompt or template version, parameters, timings, usage units, and whether it was a fallback.

## Consequences

- **+** A free-tier change degrades quality visibly instead of blocking work, and the demo can't silently show mock output.
- **+** By default, all audio stays on the laptop. Reference clips leave only for consented Kaggle runs, which are tracked and deleted. Source audio leaves only with explicit `external_transcription` consent.
- **−** Fallbacks can be clearly worse (e.g. IndicTrans2 has no rationale or audience adaptation). That's shown to the reviewer, and the evaluation reports which adapter produced each output.
- **−** Local CPU models compete with the web app for laptop RAM and CPU. Peak RAM is measured in the spike.
- **−** Free-tier limits aren't always published (Gemini's are only visible in AI Studio), so the ledger's warnings use observed limits.
- **Viva in 2 minutes:** "Every AI stage has a free primary, a free plan B and a test-only mock. Whichever one ran is shown to the reviewer, mocks can never be exported, voice data never goes to a free-tier LLM, and we spend nothing."

### Implementation note (2026-10-12; approved by the user; no decision changed)
These notes come from the live Gemini trial (`docs/trials/2026-10-12-gemini-live-trial.md`).
- **Audit semantics for provider skips:** when a real adapter is passed over, the audit log records `PROVIDER_SKIPPED` with the stage, the adapter and the reason.
  - This covers the data-use rule and provider failures, which are reasons starting `QuotaExhausted:`, `RateLimited:`, `Unavailable:` or `ProviderOutputInvalid:`.
  - It is recorded even when the whole chain fails (`NoProviderAvailable`, the normal case in demo mode).
  - Localization records it per scene; the meaning check records it per segment, with `segment_id`.
  - "Not configured" skips are not audited.
- **Audit semantics for fallbacks:** `PROVIDER_FALLBACK` records the adapter that ran and the names it ran `after`.
- **Message rule:** provider error messages go into the append-only audit log, so they must never contain provider input or output, or a key.
- **Gemini 429s:** Google's QuotaFailure `quotaId` separates a daily quota ("PerDay", giving `QuotaExhausted`) from a shorter limit (giving `RateLimited`). A `RateLimited` is retried once if RetryInfo asks for a wait of 20 s or less and the call stays within 75 s.
- **[MEASURED]** The free-tier limit seen for `gemini-3.5-flash` was 20 requests per day per project per model. Both Gemini adapters share that pool.

