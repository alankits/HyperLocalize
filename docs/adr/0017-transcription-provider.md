# ADR 0017: Transcription (English ASR) provider

**Status:** Pending spike results (provisional decision recorded 2026-10-05). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §6.7; `docs/SPIKE_PLAN.md` M1

## Context

The source language is **English**, spoken by team members (likely Indian-accented English [INFERRED]). The pipeline needs word-level timestamps to build segments and scenes. Hosted only, no GPU, ₹2,000/month. Facts below were checked on 2026-10-05.

## Options Considered

| Candidate | Verified facts | Training / retention |
|---|---|---|
| Groq `whisper-large-v3` (or `-turbo`) | $0.111/hour (turbo $0.04/hour). Word timestamps via `timestamp_granularities`. Free plan: 20 requests/min, 2,000/day, 7,200 audio-seconds/hour, 28,800/day. 25 MB file limit on the free tier. | Groq states it does not use inputs for training. Inputs and outputs may be stored for 30 days unless Zero Data Retention is enabled. |
| Sarvam Saaras v4 | Supports Indian English among 23 languages. ₹30/hour (₹45/hour with diarisation). | Sarvam's privacy policy and Trust Center statements **conflict** on training use. Opt out and confirm before sending voice. [UNVERIFIED which applies to the API] |
| ElevenLabs Scribe v2 | 90+ languages | Credit cost per minute **[UNVERIFIED]** |

## Decision (provisional)

Groq `whisper-large-v3`, with Zero Data Retention enabled, as the provisional choice: it has a free tier, word timestamps and a clear no-training statement. Sarvam Saaras v4 is the comparison candidate (it may handle Indian-accented English better). Spike decision rule 2 decides. Speaker assignment is done by a human in the UI (at most 2 speakers), not by automatic diarisation.

## Consequences

- **+** Transcription cost is negligible within the budget.
- **−** The 25 MB free-tier limit means audio must be extracted and compressed (e.g. mono 16 kHz) before upload. For clips up to 5 minutes this is easily met.
- **Viva in 2 minutes:** "English transcription is a solved, cheap problem. We picked a hosted Whisper with word timestamps and no training on our data, and we measured its error rate on numbers and terms, because those matter downstream."
