# ADR 0018: Tamil speech synthesis: stock voice and cloned voice

> **Amended by ADR 0021 (2026-10-22):** MMS-TTS Tamil is now the implemented stock voice (`mms_tts_tamil`, stock tier only). The cloned-voice tier is unchanged and still pending. ADR 0021 takes precedence where they differ.

**Status:** Pending spike results (provisional decision recorded 2026-10-05; revised the same day for zero budget). Not approved.
**Source:** ADRs 0005, 0006, 0015, 0019; `docs/THIRD_PARTY_TERMS.md`; `docs/SPIKE_PLAN.md` M4–M6, M9

## Context

The pipeline needs Tamil speech: `STOCK_VOICE` and, if viable, `CLONED_VOICE`. **Zero budget**, CPU-only laptop, Kaggle GPU in batch (about 30 h/week). Every option needs a free alternative and a mock (ADR 0005).

## Options Considered

| Option | Use | Licence / terms | Runtime | Known facts |
|---|---|---|---|---|
| **IndicF5** | `CLONED_VOICE` | Model card MIT; **treated as non-commercial**; gated; explicit voice-owner permission required | Kaggle GPU (batch) or local CPU | Needs reference clip + transcript; 24 kHz. CPU speed **unknown** (spike M6). |
| **MMS-TTS Tamil** (`facebook/mms-tts-tam`) | `STOCK_VOICE` | **CC-BY-NC-4.0** | Local CPU | VITS, 36.3M parameters, single speaker; fixed seed needed |
| **Indic Parler-TTS** | `STOCK_VOICE` | **Apache-2.0**; gated | Local CPU (speed unknown) or Kaggle | 0.9B parameters; Tamil speakers "Jaya" (recommended), "Kavitha"; prompt-controlled style |
| ElevenLabs free plan | **Dropped after review** | Non-commercial; attribution required | Hosted | Two local stock voices already exist |
| Paid cloning (ElevenLabs Starter, Sarvam), Google ICV, Azure Personal Voice | — | — | — | **Excluded**: paid or restricted |

## Decision (provisional)

- **Stock voice chain:** MMS-TTS ↔ Indic Parler-TTS (order decided by spike M4/M6). `MockSpeechSynthesisProvider` is **for tests only**, never in the live chain (ADR 0005).
- **Cloned voice chain:** IndicF5 on local CPU (live or overnight) → IndicF5 on Kaggle batch (**only if needed**, per spike rule 6 and ADR 0019) → **mode fallback to `STOCK_VOICE`**. `MockSpeechSynthesisProvider` is for tests only.
- **Voice profile** = reference clip + transcript in our media storage. Uploaded to Kaggle only for a batch run, then deleted (ADR 0006, 0019).
- The demo plan depends on IndicF5's CPU speed (ADR 0012, spike §6).

## Consequences

- **+** No paid service, and no third-party voice-clone object.
- **−** The whole stack is non-commercial (MMS-TTS; IndicF5 by our conservative reading). A future commercial version would need different models; stated.
- **−** There is no second independent free Tamil cloning model. Resilience comes from two runtimes plus the governed stock-voice fallback.
- **Viva in 2 minutes:** "Stock Tamil voices come from open-source models running on our laptop. Cloned voices come from IndicF5, on a free Kaggle GPU in advance or on our CPU live. When neither is possible, the system falls back to a labelled stock voice rather than failing."
