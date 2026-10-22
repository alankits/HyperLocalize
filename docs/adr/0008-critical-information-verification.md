# ADR 0008: Critical-information verification: rule-based hard checks + AI flags

> **Amended by ADR 0022 (2026-10-22):** Tamil number words 0–100 are parsed (a wrong number word FAILS); ambiguous words and larger numbers stay UNVERIFIABLE. ADR 0022 takes precedence where they differ.

**Status:** Accepted (approved by the user 2026-10-05). History: proposed 2026-10-04; revised 2026-10-05: English → Tamil, ADR review, independent review, which scaled down the number parser.
**Source:** `docs/PHASE0_DISCOVERY.md` §4.3, §9

## Context

HyperLocalize is a general localization workflow. It is suited to important information (for example health, food, water, energy), where a wrong number, unit or term causes harm. AI translation output is a draft (CLAUDE.md §4). The checks below are specified for the **MVP language pair, English → Tamil** (Q3). Other language pairs would need their own normalisers and lexicons [INFERRED] *(framing note 2026-10-06, `docs/PRODUCT.md`)*. Tamil output brings specific difficulties:

- **Numbers** may appear as Western digits (`5`), Tamil digits (`௫`, U+0BE6–U+0BEF), the non-positional Tamil numerals ௰ (10), ௱ (100) and ௲ (1000), or as words. Number words are inflected and combine through sandhi (e.g. இருபத்தைந்து = 25), and large numbers use the Indian system (லட்சம் = lakh, கோடி = crore; digit grouping like 1,00,000).
- **Units** may be kept in Latin script (`mg`, `ml`) or written as Tamil abbreviations or words. The exact Tamil forms in our lexicon are to be confirmed by the raters.
- **Glossary terms** inflect: Tamil is agglutinative, so a required term can appear with case suffixes, and the stem ending can change, so exact string matching fails.
- **Negation is usually built into the verb** (negative verb forms, prohibitive endings, or separate words such as இல்லை / வேண்டாம்), so there is often no separate token that a rule could check.

## Options Considered

| Criterion | Human review only | Rule checks for everything, including negation | Rule checks for numbers/units/terms + AI flags for meaning reversal + human review | AI checks only |
|---|---|---|---|---|
| Number, unit and term errors caught reliably | Depends on reviewer attention | Yes | Yes | No guarantee |
| Tamil negation built into the verb | Reviewer | Poor (many false alarms and misses) | AI flags as an aid; the human decides | AI flags only |
| Honest claim possible | "Reviewed" | Overclaims for negation | "Rule-checked" for numbers, units and terms; "flagged for review" otherwise | "AI-checked" (weak) |
| Complexity | Low | High (Tamil morphology) | Medium | Low–medium |

## Decision

### Hard rule-based checks (deterministic code, unit-tested)

**Numbers.** Extract the numbers from the English source and from the Tamil target, normalise both, and compare them as **multisets** (same values, same counts).

The **source normaliser** handles digits, decimals, ranges, times and English number words.

**MVP scope** *(reduced after independent review: a full Tamil number-word parser is too much for 4 students in 5 months, and pays off little)*:
1. The translation prompt **instructs the model to write all numbers as digits** in `subtitle_text`.
2. The target normaliser parses **Western digits** (with Western 1,000,000 and Indian 10,00,000 grouping, and decimals) and **Tamil digits ௦–௯**.
3. **Any Tamil number word**, and any of the non-positional numerals ௰ ௱ ௲, is **not parsed**. The result is **`UNVERIFIABLE`**, which a reviewer must resolve. This is the **fail-safe rule**: nothing that looks like a number is ever passed silently.

**Stretch scope** (only if time allows, and measured against the raters' labels): a bounded Tamil number-word lexicon (units to crore, common combined and case-suffixed forms; decimal word புள்ளி).

**Units.** A per-language unit lexicon maps Latin and Tamil forms to one canonical unit (`mg`, `ml`, `°C`, `km`, `L`, …). The checks are:
- every source unit must appear in the target;
- a converted unit is accepted only if the project's audience profile declares that conversion, **and** the converted value matches.

Tamil unit forms are added to the lexicon from the raters' review, not from memory.

**Glossary and do-not-translate terms.** Each glossary entry stores the required Tamil term **plus a list of accepted forms** (inflected variants), which the raters fill in. Matching accepts any listed form, or the stem followed by a suffix. Do-not-translate terms must appear unchanged (Latin script) or in a declared transliteration.

**Structural checks.** Empty output; untranslated output (the target is the same as the source, or is mostly Latin script); length versus the timing budget.

**Effect.** A failed or `UNVERIFIABLE` hard check **blocks approval** until the segment is fixed, or until a reviewer overrides the check with a written reason. Overrides are audited and listed in the export's quality report.

### AI-flagged checks (advisory, via `MeaningCheckProvider`, ADR 0005)

- negation and meaning reversal, e.g. "do not boil" vs. "boil", or a prohibitive turned into a permissive;
- omissions and additions;
- register mismatch.

A flagged segment requires **explicit reviewer acknowledgement** before approval. AI flags are never described as verification.

### Human review of every segment

This remains mandatory. A segment with no flags is not assumed correct.

### Speech script vs. subtitle script

Subtitles keep digits, because they are easier to read. Whether the Tamil TTS reads digits, decimals and units correctly is **measured in the spike (M4)**. If it doesn't, a deterministic number-to-Tamil-words step produces the **speech script**, and the number check runs on **both** scripts.

### Wording rule

In the UI, docs and viva, "rule-checked" applies only to numbers, units, glossary terms and the structural checks. Everything else is "flagged for human review" or "human-reviewed".

## Consequences

- **+** A precise claim that can be defended, and that is measurable per layer with seeded errors: rule-check catch rate, AI-flag catch rate, reviewer catch rate (`docs/SPIKE_PLAN.md`, `PHASE0_DISCOVERY.md` §8.4).
- **+** The fail-safe `UNVERIFIABLE` result means gaps in the Tamil normaliser cost reviewer time rather than silently letting errors through.
- **+** The MVP parser is small (digits only), so it can be fully unit-tested.
- **−** If the model ignores the digits instruction, there will be more `UNVERIFIABLE` results. That rate is measured in spike M3.
- **−** The glossary accepted-forms lists are manual work and will be incomplete.
- **−** False alarms cost reviewer time. Overrides with reasons exist for this.
- **−** The AI flagger adds cost and latency per segment. It uses free-tier quota, is measured in the spike, and has a fail-safe `CHECK_UNAVAILABLE` flag when no checker is available (ADR 0005).
- **Viva in 2 minutes:** "Numbers, units and glossary terms are checked by code, including Tamil digits. Anything the code can't parse, such as numbers written as words, is flagged for a human instead of passed. Tamil negation lives in the verb, so a rule can't check it reliably. An AI flags possible reversals, and a human must look at every flag and every segment."
