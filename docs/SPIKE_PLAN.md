# HyperLocalize: Technical Spike Plan

| | |
|---|---|
| **Date** | 2026-10-04 |
| **Status** | PLAN ONLY. **Not run.** Needs your approval. |
| **Purpose** | Produce measured evidence to decide the group B1 ADRs (`PHASE0_DISCOVERY.md` §12) before they are finalised |
| **Language pair** | `{SOURCE_LANG} → {TARGET_LANG}`: **[UNKNOWN], waiting on Q3** |
| **Budget cap** | `{SPIKE_BUDGET}`: **[UNKNOWN], waiting on Q4** |

All results from this spike are **MEASURED RESULTS on one clip**. They are directional evidence for choosing providers, not proof of quality. The full evaluation (`PHASE0_DISCOVERY.md` §8, slice S4) is where quality claims come from.

---

## 1. Prerequisites (blocking)

| # | Prerequisite | Why |
|---|---|---|
| P1 | **Q3**: language pair | Every candidate must support it; metric choice depends on it (see M1) |
| P2 | **Q4**: budget and GPU access | Decides whether local models are candidates at all; sets the spending cap |
| P3 | **Q6**: may voice and video go to third-party providers? | If not, all hosted candidates are excluded |
| P4 | **Q7**: at least one, ideally two, bilingual raters | Needed for the reference translation and the human ratings in M2/M3. Without them, M2/M3 report automatic metrics only and say so. |
| P5 | Written consent from the team member(s) whose voice is recorded, naming each provider the audio will be sent to | Identity data is used even in a spike (CLAUDE.md §5) |
| P6 | Your approval of this plan and of the spending cap | CLAUDE.md §3 (ongoing cost, real voices) |

## 2. Test material

**One clip, 60–120 seconds, recorded by the team**, 1–2 consenting speakers, on a critical-information topic (e.g. a health-information explainer; final topic is Q17).

The script is **written first** so that it deliberately contains:

| Content | Minimum count | Used by |
|---|---|---|
| Numbers (including a dosage, a decimal, a range, a time) | 10 | M1, M2 rule checks |
| Units (mg, ml, °C, litres, km, …) | 5 | M1, M2 |
| Glossary terms (domain terms with a fixed target translation) | 5 | M1, M2, M3 pronunciation |
| Negated instructions ("do not…", "never…") | 5 | M2 meaning-reversal flags |
| Idioms or culturally specific phrases | 2 | M2 adaptation |
| Short and long sentences | mix | M4 timing |

Also prepared:
- **Reference transcript:** the written script, corrected by hand to what was actually said.
- **Segment boundaries:** start and end times marked by hand on the recording (for M1 timing accuracy and as segment slots for M4).
- **Reference translation:** produced by a bilingual rater **before** seeing any system output, to avoid anchoring.
- **Glossary file:** source term → required target term.
- **Seeded-error set:** 5 copies of segments with deliberately reversed meaning (negation removed or flipped) plus 5 with a wrong number, unit or term, used to test the checks in M2.
- **Clean reference voice sample** from each consenting speaker (as long as the candidate cloning providers require), for M3.

**Data handling.**
- Media is never committed to git (already covered by `.gitignore`).
- Record which file was sent to which provider and when.
- After the spike, delete uploaded voices and files at each provider using its deletion mechanism, and record that this was done.
- Raw transcripts and audio do not go into the docs. Only metrics and short anonymised examples do.

## 3. Candidates and hard gates

Candidates are listed **per stage after Q3/Q4/Q6 are answered**, so I don't name providers that may not support your language. Each candidate must pass these **hard gates** before it is measured. A candidate that fails a gate is recorded as excluded, with the reason.

| Gate | Check (document review) |
|---|---|
| G1 Language | Officially documented support for `{SOURCE_LANG}` (ASR) / `{TARGET_LANG}` (translation, TTS) |
| G2 Licence / terms | Permits this project's use (check for non-commercial-only model licences and for terms that allow training on our data) |
| G3 Data policy | Allowed under Q6; data region and retention noted |
| G4 Deletion (voice only) | Voice profiles can be deleted through an API (required by ADR 0005 / 0006) |
| G5 Cost | Spike usage fits within `{SPIKE_BUDGET}` |

Planned comparison slots:

| Stage | Slots |
|---|---|
| Transcription | 1 local Whisper-family model (if GPU or acceptable CPU speed) · 1 hosted ASR |
| Translation | **T0** NMT baseline · **T1** LLM without context · **T2** LLM with full textual context (transcript window, speaker, audience profile, glossary, timing budget) |
| Meaning-reversal flagger | The T1/T2 LLM in a separate checking pass (one prompt) |
| Speech synthesis | **V0** stock (non-cloning) TTS · **V1** hosted voice cloning · **V2** local voice cloning (only if GPU + licence pass) |

## 4. Measurements

All spike scripts live in a `spike/` folder. They are throwaway, are never imported by the application, and are committed only for reproducibility. Each script records the provider, model identifier and version, prompt text and version, parameters, date, and hardware.

### M1: Transcription accuracy

| | |
|---|---|
| **Metrics** | Word error rate (WER) **and** character error rate (CER) against the reference transcript. **Critical-token error rate**: % of the script's numbers, units and glossary terms transcribed wrongly. **Boundary error**: mean absolute difference (ms) between ASR segment start/end and the hand-marked boundaries. **Real-time factor**: processing time ÷ audio duration. |
| **Method** | Normalisation rules are fixed *before* scoring (case, punctuation, numerals written as digits vs. words). Scored with a standard library (e.g. `jiwer`; verify). Each candidate is run 3 times and the median reported for timing. CER is reported alongside WER because WER over-penalises agglutinative languages, where one word carries several morphemes. |
| **Decides** | **ASR provider ADR** (B1). The boundary error also informs scene segmentation (§6.7). |

### M2: Translation quality

| | |
|---|---|
| **Input** | The **reference transcript**, so ASR errors don't contaminate the comparison. Optionally also the best M1 output, to see end-to-end effects. |
| **Systems** | T0, T1, T2 |
| **Automatic metrics** | chrF against the reference translation (e.g. via `sacreBLEU`; verify). A learned metric (e.g. COMET) **only if** its model documents support for `{TARGET_LANG}`; otherwise omitted and the omission noted. |
| **Human metrics** | For each segment, the bilingual rater(s) label errors with MQM-style categories (accuracy, fluency, terminology, style, locale) and severity (critical / major / minor), **blind to which system produced it** (randomised order). Then a blind pairwise preference: T2 vs. T0, T2 vs. T1. |
| **Rule checks** | Run a throwaway prototype of the hard checks (numbers, units, glossary terms; ADR 0008) on every output. Report the pass rate per system and the checks' precision and recall against the rater's labels. |
| **AI flags** | Run the meaning-reversal flagger on the seeded-error set and on the clean outputs. Report **recall** on seeded reversals and the **false-flag rate** on clean segments. |
| **Cost and latency** | Tokens or characters, and wall-clock time, per system (feeds M5 and M6). |
| **Caveat** | About 20–30 segments and one or two raters. **Directional only.** If T2 doesn't beat T0 here, that is recorded honestly but doesn't end context-awareness; the S4 ablation on 3–5 clips decides. |
| **Decides** | **Translation method and provider ADR** (B1), **MeaningCheckProvider** choice, and the realistic limits of the ADR 0008 checks for this language. |

### M3: Speech synthesis quality

| | |
|---|---|
| **Input** | The **same fixed target text** for every system (the reference translation), so differences come only from the TTS. |
| **Systems** | V0, V1, V2 |
| **Intelligibility** | ASR round-trip: transcribe the synthesised audio with the best `{TARGET_LANG}`-capable ASR and compute CER against the input text. The same ASR is used for every system so the comparison is fair. This measures the ASR too, so it is a relative measure only. |
| **Critical-content pronunciation** | A bilingual listener checks every number, unit and glossary term: correct / wrong / unclear. |
| **Naturalness** | Mean opinion score (1–5) from available listeners. Report *n*. With a small *n* this is indicative only. |
| **Speaker similarity (objective)** | Cosine similarity between speaker-verification embeddings (e.g. an ECAPA-TDNN model; verify) of the original speaker and the synthesised voice. **V0 (stock voice) serves as the control.** Cross-language similarity is naturally lower, so only the comparison with the control is meaningful. |
| **Speaker similarity (subjective)** | Listeners who know the speaker answer "same person?" on a 1–5 scale. |
| **Decides** | **Identity definition ADR** (B1): is `CLONED_VOICE` viable in `{TARGET_LANG}` for the MVP? Also the **speech synthesis and voice-profile provider ADR** (B1). |

### M4: Timing fit

| | |
|---|---|
| **Metric** | For each segment, synthesised duration ÷ source slot duration. Report the distribution and the % of segments within ±15% (the ±15% band is an **assumed working threshold**, to be revisited). |
| **Method** | Compare T1/T2 output without vs. with the length constraint in the prompt, synthesised with V0 at normal speed and at the provider's bounded speed adjustment. |
| **Decides** | Whether length-constrained translation plus speed adjustment is enough for the MVP, or whether isochrony needs more work (part of the translation ADR). This also sets the realistic TARGET for "timing fit" in `docs/EVALUATION.md`. |

### M5: Latency

| | |
|---|---|
| **Metrics** | Wall-clock time per stage per minute of source audio. Real-time factor. **Longest single synthesis call** (per segment). |
| **Method** | 3 runs each, median and max reported. First run (cold) reported separately. Hardware, network and date recorded. |
| **Decides** | **Hosting / GPU ADR** (B2). Job sizing (ADR 0003). The **measured upper bound on how long revocation takes to stop a job** (ADR 0006 says it is bounded by the longest single provider call). |

### M6: Cost per minute

| | |
|---|---|
| **Metric** | Cost per minute of source video, per stage and in total, for each candidate combination. |
| **Method** | Metered usage units from each provider (audio seconds, input/output tokens, characters) × the provider's published price **on the spike date**, with the price page URL and date recorded. For local models: hardware used and run time (no invented money figure). The cost of the AI-flag pass and of the context (T2's longer prompts) is shown separately. |
| **Decides** | All B1 provider ADRs, and whether the MVP fits the Q4 budget. |

### M7: Provider data handling (document review, not a measurement)

| | |
|---|---|
| **Check** | Retention period, whether data is used for training (and whether you can opt out), data region, voice-deletion API and its documented behaviour, consent or attestation requirements for voice cloning |
| **Decides** | Gates G2–G4, ADR 0005 provider eligibility, ADR 0006 provider-side deletion behaviour, and the consent form wording (Q6) |

## 5. Decision rules (fixed before seeing results)

These rules are written now so that the results can't be fitted to a preferred answer afterwards.

1. **Gates before quality.** A candidate that fails G1–G5 is excluded, however good it is.
2. **ASR:** choose the lowest critical-token error rate. If within 2 percentage points, choose the lower CER. If still tied, prefer local (privacy), then lower cost.
3. **Translation:** choose the system with the fewest critical and major MQM errors. Ties are broken by rule-check pass rate, then cost. If T2 is not better than T0, the MVP still implements the T2 design behind the interface (it is needed for the rationale and the audience profile), and the S4 ablation decides whether the claim holds. The result is reported either way.
4. **Identity (`CLONED_VOICE`):** adopt for the MVP only if a cloning candidate passes G1–G5 **and** its intelligibility and critical-content pronunciation are no worse than V0 by more than a small agreed margin (set with you before the spike) **and** its speaker similarity is above the V0 control. **Otherwise** the MVP uses `STOCK_VOICE` only, consent governance is still built and demonstrated (ADR 0006), and the identity claim is narrowed. That outcome is **escalated to you** before the ADR is written.
5. **Budget:** if the cheapest acceptable combination exceeds the Q4 budget for the planned demo volume, escalate to you before choosing.

## 6. Outputs

- `docs/EVALUATION.md` (created at this point): each metric with its definition, TARGET (set after the spike), **MEASURED RESULT** (spike value, labelled "spike, 1 clip, n = …"), and method.
- A short spike results section listing excluded candidates and why, measured values per candidate, and the decision each rule produced.
- Group B1 ADR drafts, citing the measured values, for your approval.
- `spike/` scripts, for reproducibility. No media and no raw transcripts are committed.

## 7. Proposed time box and risks

**Time box:** about 5 working days for one person [PROPOSED]. To be adjusted once team size is known (Q2).

| Risk | Mitigation |
|---|---|
| No candidate supports `{TARGET_LANG}` well enough | Rule 4 fallback (stock voice); escalate. This may justify changing the language pair. |
| No bilingual rater available | Automatic metrics only, clearly labelled. Human evaluation is moved to S4, with the raters sourced by then. |
| Provider terms forbid our use or retain voices | Excluded at gate G2/G4 |
| Spending overrun | Hard cap `{SPIKE_BUDGET}`; usage checked after each stage |
| One clip is not representative | Stated in every result; the full evaluation uses 3–5 clips |
