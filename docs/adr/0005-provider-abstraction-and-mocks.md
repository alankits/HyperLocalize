# ADR 0005: AI provider abstraction: free provider chains, mock providers, zero-spend policy

**Status:** Proposed (2026-10-04; revised 2026-10-05 after the ADR review; **revised again 2026-10-05 for the zero-budget Q4 answer**). Not yet approved.
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
| Transcription (English) | Groq `whisper-large-v3` (free plan) | **faster-whisper on local CPU** (MIT) | `MockTranscriptionProvider` |
| Translation (context-aware) | Gemini Flash (**free tier**, with the data-use rule below) | Groq-hosted open LLM (free plan) → last resort **IndicTrans2 on local CPU** (context-free, marked) | `MockTranslationProvider` |
| Meaning-check (AI flags) | An LLM from a different family to the translator (Groq or Gemini) | The other one. If both are unavailable, every segment gets a **`CHECK_UNAVAILABLE`** flag that needs manual acknowledgement (fail-safe). | `MockMeaningCheckProvider` |
| Stock Tamil voice | MMS-TTS Tamil or Indic Parler-TTS (**local CPU**) | The other local model → ElevenLabs free plan (non-commercial, attribution) | `MockSpeechSynthesisProvider` |
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

**Data-use rule for free tiers.** Content may be sent to a free tier only if that tier's terms are compatible with it:
- **Gemini free tier:** only team-authored, scripted, non-personal **text**; never audio; never third-party content (the terms say not to submit personal information).
- **Voice data** (reference clips, cloned speech) goes only to local models or to Kaggle private datasets, never to a free-tier LLM.

The processors used are recorded in the Consent and in the evidence manifest.

**Local model runtime.** Local models (faster-whisper, IndicTrans2, MMS-TTS, Indic Parler-TTS, IndicF5 on CPU) run in a **separate inference subprocess** owned by the worker. The model stays loaded between calls. The worker can **kill** the subprocess to cancel immediately (ADR 0006) and restarts it on the next call.

**Recorded on every call:** adapter, model identifier and version, prompt or template version, parameters, timings, usage units, and whether it was a fallback.

## Consequences

- **+** A free-tier change degrades quality visibly instead of blocking work, and the demo can't silently show mock output.
- **+** Voice data stays on the laptop or in private Kaggle datasets that we delete.
- **−** Fallbacks can be clearly worse (e.g. IndicTrans2 has no rationale or audience adaptation). That's shown to the reviewer, and the evaluation reports which adapter produced each output.
- **−** Local CPU models compete with the web app for laptop RAM and CPU. Peak RAM is measured in the spike.
- **−** Free-tier limits aren't always published (Gemini's are only visible in AI Studio), so the ledger's warnings use observed limits.
- **Viva in 2 minutes:** "Every AI stage has a free primary, a free plan B and a test-only mock. Whichever one ran is shown to the reviewer, mocks can never be exported, voice data never goes to a free-tier LLM, and we spend nothing."
