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
| **Gemini Flash, free tier** | T1/T2 primary candidate | ₹0 | Used for training; human review possible | Sent only when `Project.data_classification = SCRIPTED_TEAM` (enforced in the chain, ADR 0005) |
| **Groq-hosted open LLM** (production models only: `llama-3.3-70b-versatile` or `openai/gpt-oss-120b`; preview models dropped after review because they're unstable), free plan | T1/T2 alternative; meaning-check | ₹0 | No training | Tamil quality unknown. **One** is chosen by a 5-segment pre-screen in the spike. |
| **IndicTrans2 En→Indic distilled 200M**, local CPU (MIT) | **T0 baseline** and **last-resort fallback** | ₹0 | Stays local | Context-free, no rationale; built for Indic languages |
| Google Cloud Translation, Claude API | — | Needs billing or paid credits | — | **Excluded** (zero spend) |

## Decision (provisional)

- **Method:** an LLM with structured textual context (T2), returning `subtitle_text`, `speech_text`, `adaptation_type`, `rationale`, `uncertainty_flags`. Prompts are versioned.
- **Chain** (ADR 0005): Gemini free tier → Groq open LLM → IndicTrans2 (local; marked "fallback: no context, no rationale") → `MockTranslationProvider` (tests only).
- **Baseline:** IndicTrans2, kept permanently for the evaluation ablation (T0).
- **Meaning-check:** same-family vs. different-family checker is **provisional, decided by spike rule 7**. If no checker is available, every segment gets `CHECK_UNAVAILABLE`, which needs manual acknowledgement.
- **Primary provider:** chosen by spike rule 3.

## Consequences

- **+** Translation keeps working if Gemini or Groq quotas change, because IndicTrans2 runs locally.
- **+** IndicTrans2 is built specifically for Indic languages, so it is expected to be a fair baseline for Tamil [INFERRED; not measured].
- **−** Free-tier Gemini is unsuitable for real third-party or personal content. A future deployment would need a paid tier or a local model; that is stated.
- **−** One clip and two raters give directional results only; the S4 ablation decides the context-awareness claim.
- **Viva in 2 minutes:** "A free LLM translates with context and gives a reason. A second, different LLM looks for meaning reversals. If the free tiers fail, an open-source Indic translator on the laptop takes over, and the reviewer is told. We compare all of it against that same open-source baseline."
