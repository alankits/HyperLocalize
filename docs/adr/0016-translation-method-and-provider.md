# ADR 0016: Context-aware translation method and provider (English → Tamil)

**Status:** Pending spike results (provisional decision recorded 2026-10-05). Not approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §4; ADR 0008; `docs/SPIKE_PLAN.md` M2

## Context

The target is Tamil for high-stakes information. The budget is ₹2,000/month with hosted APIs only (Q4). "Context-aware" must be testable: a fixed set of inputs, compared against a context-free baseline. Two bilingual English–Tamil raters are available (Q7). Facts below were checked on 2026-10-05; sources are in `docs/SPIKE_PLAN.md` §3.

## Options Considered

| Criterion | NMT API (e.g. Google Cloud Translation NMT, Sarvam Mayura) | **LLM with structured textual context** (transcript window, speaker, audience profile, glossary, timing budget) | LLM + visual context |
|---|---|---|---|
| Audience, register, glossary, reviewer instructions | Limited | **Yes** | Yes |
| Per-segment rationale for the reviewer | No | **Yes** | Yes |
| Cost | Free tier or very low | Low (estimates in the spike plan) | Higher |
| Role | **Baseline** (T0) | **Candidate method** (T2) | Stretch only (S5) |

**Provider candidates for T1/T2 and the AI meaning-check:**

| Candidate | Verified facts | Notes |
|---|---|---|
| Gemini Flash (current: Gemini 3.8 Flash) | Paid $0.75 / $3.75 per 1M input/output tokens until 2026-12-31, then $1.50 / $7.50. Free tier exists, but **free-tier content is used to improve Google's products**. | Use the **paid tier** for project data. Note the price rise on 2027-01-01, inside the 5-month window. |
| Claude Sonnet 5.5 / Claude Haiku 4.5 | $2 / $10 and $1 / $5 per 1M input/output tokens; small free credits for new users | Tamil quality to be measured |
| T0 baseline: Google Cloud Translation NMT | 500,000 characters/month free, then $20 per 1M characters | Context-free baseline |

## Decision (provisional)

- **Method:** an LLM with structured textual context (T2), returning per segment: `subtitle_text`, `speech_text`, `adaptation_type`, `rationale`, `uncertainty_flags`. Prompts are versioned.
- **Baseline:** Google Cloud Translation NMT (T0), kept permanently for the evaluation ablation.
- **Meaning-check (AI flags, ADR 0008):** a separate prompt. The spike tests whether running it on a **different model family** from the translator catches more seeded reversals.
- **Provider:** chosen from the candidates above by spike decision rule 3. Provisional favourite: Gemini Flash (paid tier) **because of cost**, but quality decides.

## Consequences

- **+** Context-awareness can be tested (T0 vs. T1 vs. T2).
- **−** One clip and two raters give directional results only; the S4 ablation on 3–5 clips decides the claim.
- **−** The model's rationale is the model's stated reason, not a faithful explanation of how it produced the text. It is labelled that way in the UI.
- **Viva in 2 minutes:** "An LLM translates each segment with its neighbours, the speaker, the audience profile and the glossary, and gives the reviewer a reason. We compare it against plain machine translation with two bilingual raters, so we can show whether the context helps."
