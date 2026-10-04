# ADR 0016: Context-aware translation method and providers (English → Tamil)

**Status:** Pending spike results (provisional decision recorded 2026-10-05; revised the same day for zero budget). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §4; ADRs 0005, 0008; `docs/THIRD_PARTY_TERMS.md`; `docs/SPIKE_PLAN.md` M2–M3

## Context

Tamil translation of high-stakes information, at **zero budget** (free tiers and open-source models only). "Context-aware" must be testable against a context-free baseline. Two bilingual raters (Q7).

Free-tier terms matter:
- the **Gemini API free tier** uses submitted content to improve Google products, allows human review, and says not to submit personal information;
- **Groq's free plan** states no training on inputs.

## Options Considered

| Option | Role | Cost | Data terms | Notes |
|---|---|---|---|---|
| **Gemini Flash, free tier** | T1/T2 primary candidate | ₹0 | Used for training; human review possible | Only team-authored, scripted, non-personal text may be sent |
| **Groq-hosted open LLM** (`llama-3.3-70b-versatile`, `openai/gpt-oss-120b`, preview `qwen/qwen3.8-27b`), free plan | T1/T2 alternative; meaning-check | ₹0 | No training | Tamil quality unknown; measured |
| **IndicTrans2 En→Indic distilled 200M**, local CPU (MIT) | **T0 baseline** and **last-resort fallback** | ₹0 | Stays local | Context-free, no rationale; built for Indic languages |
| Google Cloud Translation, Claude API | — | Needs billing or paid credits | — | **Excluded** (zero spend) |

## Decision (provisional)

- **Method:** an LLM with structured textual context (T2), returning `subtitle_text`, `speech_text`, `adaptation_type`, `rationale`, `uncertainty_flags`. Prompts are versioned.
- **Chain** (ADR 0005): Gemini free tier → Groq open LLM → IndicTrans2 (local; marked "fallback: no context, no rationale") → `MockTranslationProvider` (tests only).
- **Baseline:** IndicTrans2, kept permanently for the evaluation ablation (T0).
- **Meaning-check:** run by an LLM from a **different family** to the translator (e.g. Gemini translates, Groq-hosted Llama or gpt-oss checks). If no checker is available, every segment gets `CHECK_UNAVAILABLE`, which needs manual acknowledgement.
- **Primary provider:** chosen by spike rule 3.

## Consequences

- **+** Translation keeps working if Gemini or Groq quotas change, because IndicTrans2 runs locally.
- **+** IndicTrans2 is a stronger, fairer baseline for Tamil than a general-purpose machine translation API.
- **−** Free-tier Gemini is unsuitable for real third-party or personal content. A future deployment would need a paid tier or a local model; that is stated.
- **−** One clip and two raters give directional results only; the S4 ablation decides the context-awareness claim.
- **Viva in 2 minutes:** "A free LLM translates with context and gives a reason. A second, different LLM looks for meaning reversals. If the free tiers fail, an open-source Indic translator on the laptop takes over, and the reviewer is told. We compare all of it against that same open-source baseline."
