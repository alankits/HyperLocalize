# ADR 0017: Transcription (English ASR) provider

**Status:** Pending spike results (provisional decision recorded 2026-10-05; revised the same day for zero budget). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7; ADR 0005; `docs/SPIKE_PLAN.md` M1

## Context

The source is English spoken by team members (likely Indian-accented [INFERRED]). The pipeline needs word-level timestamps. **Zero budget**, CPU-only laptop.

## Options Considered

| Option | Facts (checked 2026-10-05) | Data terms |
|---|---|---|
| **Groq `whisper-large-v3`**, free plan (no card) | Word timestamps. Free plan: 20 requests/min, 2K/day, 7,200 audio-s/hour, 28,800 audio-s/day; 25 MB file limit. | No training. 30-day storage unless ZDR is on (we turn it on). |
| **faster-whisper, local CPU** (MIT) | int8 on CPU; word timestamps. The repo's benchmark is the small model on an i7-12700K with 8 threads (our laptop will differ, so we measure). | Stays local |
| Sarvam Saaras | — | **Excluded** (₹100 one-off credits; conflicting training terms) |

## Decision (provisional)

Chain: Groq `whisper-large-v3` → faster-whisper (local CPU; model size picked by the spike) → `MockTranscriptionProvider` (tests only). Spike rule 2 may make faster-whisper the primary if its accuracy and speed are acceptable, because it has no quota at all. Speakers are assigned by a human in the UI.

## Consequences

- **+** Transcription can never be blocked by a quota.
- **−** CPU transcription is slower. Fine for 1–5 minute clips, measured in M1.
- **Viva in 2 minutes:** "English transcription uses free hosted Whisper, with the same model running locally as a backup. We measured error rates on numbers and terms, because those errors would carry into the Tamil."
