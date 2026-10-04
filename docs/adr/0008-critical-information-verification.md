# ADR 0008: Critical-information verification: rule-based hard checks + AI flags

**Status:** Proposed (2026-10-04). Not yet approved.
**Source:** `docs/PHASE0_DISCOVERY.md` §4.3, §9

## Context

HyperLocalize targets high-stakes information (health, food, water, energy), where a wrong number, unit or term causes harm. AI translation output is a draft (CLAUDE.md §4). Some errors can be checked reliably by rules; others cannot. Negation in particular is often part of the grammar of the target language (verb suffixes, mood, auxiliaries) and can't be token-matched reliably. The system must not call something "verified" when it is only AI-flagged.

The translation provider is not yet chosen (group B1). This ADR is independent of that choice.

## Options Considered

| Criterion | Human review only | Rule checks for everything, including negation | Rule checks for numbers/units/terms + AI flags for meaning reversal + human review | AI checks only |
|---|---|---|---|---|
| Catches number/unit/term errors reliably | Depends on reviewer attention | Yes | Yes | No guarantee |
| Handles negation embedded in grammar | Reviewer | Poorly (false alarms and misses) | AI flags as an aid; human decides | AI flags only |
| Honest claim possible | "Reviewed" | Overclaims for negation | "Rule-verified" for numbers/units/terms; "flagged for review" otherwise | "AI-checked" (weak) |
| Complexity | Low | Medium | Medium | Low–medium |

## Decision

**Hard rule-based checks** (deterministic code with unit tests):
- numbers, after normalising digits, native-script numerals, decimal and thousands separators, and number words where a per-language list exists;
- units, using a per-language unit lexicon, accepting only the conversions declared in the project's audience profile;
- glossary and do-not-translate terms, with stem or suffix-tolerant matching for languages that inflect;
- empty or untranslated output;
- length vs. timing budget.

A failed hard check **blocks approval** until the segment is fixed, or until a reviewer overrides it with a written reason (audited, and listed in the export's quality report).

**AI-flagged checks** (advisory; via `MeaningCheckProvider`, ADR 0005):
- negation and meaning reversal;
- omissions and additions;
- register mismatch.

A flagged segment requires **explicit reviewer acknowledgement** before approval. AI flags are never described as verification.

**Human review of all segments** remains mandatory. Unflagged segments are not assumed correct.

**Wording rule** for the UI, docs and viva: "rule-checked" applies only to the hard-check categories. Everything else is "flagged for human review" or "human-reviewed".

## Consequences

- **+** A precise, defensible claim about what is checked and how.
- **+** Measurable per layer with seeded errors (`PHASE0_DISCOVERY.md` §8.4): rule-check precision and recall, AI-flag recall, reviewer catch rate.
- **−** Number-word normalisers and inflection-tolerant matching are language-specific and may be incomplete for the chosen language (Q3). False alarms cost reviewer time, and misses are possible. Overrides exist for this reason.
- **−** The AI flagger adds cost and latency per segment, to be measured in the spike.
