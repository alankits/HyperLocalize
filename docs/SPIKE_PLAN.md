# HyperLocalize: Technical Spike Plan (English → Tamil)

| | |
|---|---|
| **Date** | 2026-10-05 (revision 2) |
| **Status** | PLAN ONLY. **Not run.** Needs your approval, including the spending cap. |
| **Purpose** | Produce measured evidence to decide ADRs 0015–0018 (status "Pending spike results") and to check the limits of ADR 0008 for Tamil |
| **Language pair** | English (`en`) → Tamil (`ta-IN`) (Q3) |
| **Spike spending cap** | **₹1,500** hard cap, inside the ₹2,000/month AI budget (Q4). Estimate: about ₹1,170 (§7). |
| **Raters** | 2 bilingual English–Tamil raters (Q7), called R1 and R2 |
| **Hardware** | Team laptop, no GPU; hosted APIs only (Q4) |

All results are **MEASURED RESULTS on one clip** (spike, n = 1 clip, about 30 segments). They are directional evidence for choosing providers, not quality claims. Quality claims come from the full evaluation (slice S4, 3–5 clips).

---

## 1. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| P1 | Language pair | **Done:** English → Tamil |
| P2 | Budget and GPU | **Done:** ₹2,000/month, no GPU |
| P3 | Third-party processing allowed | **Done:** yes; only the team's own voices and videos |
| P4 | Raters | **Done:** 2 raters |
| P5 | Signed consent from each recorded team member, **naming every provider** their audio will go to (Groq, Sarvam, ElevenLabs, Google) | To do |
| P6 | **Training opt-outs applied and confirmed** before any voice is uploaded: ElevenLabs "Improve the models for everyone" toggle off; Sarvam opt-out applied and confirmed in writing (their statements conflict, §3); Gemini used on the **paid** tier only; Groq Zero Data Retention on | To do |
| P7 | Your approval of this plan and the ₹1,500 cap | **Waiting** |

## 2. Test material

**One clip of 90–120 seconds**, recorded by a consenting team member (optionally two speakers), on a **health-information topic** (proposed: safe use of oral rehydration salts or a similar public-health explainer [PROPOSED; confirm the topic, Q17]).

The script is **written first** so that it deliberately contains:

| Content | Minimum | Used by |
|---|---|---|
| Numbers: a dosage, a decimal, a range, a time, a large number (≥ 1 lakh) | 10 | M1, M2 rule checks |
| Units (mg, ml, L, °C, minutes, km) | 5 | M1, M2 |
| Glossary terms (domain terms with a fixed Tamil translation, chosen by R1/R2) | 5 | M1, M2, M3 pronunciation |
| Negated instructions ("do not…", "never…", "should not…") | 5 | M2 meaning-reversal flags |
| Idioms or culturally specific phrases | 2 | M2 adaptation |
| Short and long sentences | mix | M4 timing |

Also prepared:
- **Reference transcript:** the script, corrected by hand to what was actually said.
- **Segment boundaries:** start and end times marked by hand.
- **Reference translation:** written by **R1 before seeing any system output**; R2 checks it. Limitation: R1 knows the reference when rating, which is recorded.
- **Glossary file:** English term → required Tamil term + **accepted inflected forms** (from R1/R2).
- **Tamil unit lexicon:** Latin and Tamil forms for each unit used (from R1/R2, not from memory).
- **Seeded-error set (20 items),** made by editing copies of the reference translation:

  | Seeded error type | Count | Expected to be caught by |
  |---|---|---|
  | Wrong number (Western digits) | 3 | Hard check |
  | Wrong number written as Tamil digits (௦–௯) | 2 | Hard check |
  | Wrong number written as Tamil words | 3 | Hard check (or `UNVERIFIABLE`) |
  | Wrong or missing unit | 4 | Hard check |
  | Wrong glossary term | 4 | Hard check |
  | Negation removed or flipped in the verb | 4 | AI flag (not a rule) |

  Plus 6 extra reversal or omission errors (total 10 for the AI flags), and the **clean** reference segments to measure false alarms.
- **Reference voice clip:** 10–30 s of clean speech from each consenting speaker (Sarvam's guideline is 10–30 s; ElevenLabs IVC uses short samples).

**Data handling.**
- Media is never committed to git.
- A log records which file went to which provider and when.
- After the spike, uploaded voices are deleted through each provider's delete API, and the result is recorded.
- Only metrics and short anonymised examples go into the docs.

## 3. Candidates, with checked facts

Checked on **2026-10-05** against official provider pages. Prices change. Anything not confirmed on an official page is marked **[UNVERIFIED]**.

### Transcription (English)

| Candidate | Supports source | Free tier / limits | Price | Terms relevant to us | Source |
|---|---|---|---|---|---|
| **Groq** `whisper-large-v3` (`-turbo` as a cheaper variant) | Multilingual Whisper (English is covered) | Free plan: 20 RPM, 2K RPD, 7.2K audio-s/hour, 28.8K audio-s/day; 25 MB file limit on the free tier | $0.111/h (turbo $0.04/h) | No training on inputs. May retain 30 days unless Zero Data Retention is enabled. | [STT docs](https://console.groq.com/docs/speech-to-text), [rate limits](https://console.groq.com/docs/rate-limits), [your data](https://console.groq.com/docs/your-data) |
| **Sarvam Saaras v4** | 22 Indian languages + Indian English | ₹100 free credits on signup (docs) | ₹30/hour | Privacy policy says content is used for training **unless you opt out**; Trust Center says API inputs are not used. **Conflicting**; resolve before use. | [models](https://docs.sarvam.ai/api-reference-docs/getting-started/models), [pricing](https://www.sarvam.ai/api-pricing), [privacy](https://www.sarvam.ai/privacy-policy), [trust](https://www.sarvam.ai/trust-center) |

### Translation (English → Tamil)

| Candidate | Role | Tamil | Free tier | Price | Terms | Source |
|---|---|---|---|---|---|---|
| **Google Cloud Translation (NMT)** | T0 baseline | Yes [UNVERIFIED on the language page; Tamil is widely documented, but I didn't fetch the list] | 500,000 chars/month (as a $10 monthly credit) | $20 per 1M chars | Cloud terms | [pricing](https://cloud.google.com/translate/pricing) (figures from search results on the official page; the page itself was truncated when fetched) |
| **Gemini 3.8 Flash** (paid tier) | T1/T2 candidate, meaning-check | [UNVERIFIED: Tamil quality is what the spike measures] | Free tier exists, **but free-tier content is used to improve Google's products**, so not used | $0.75 / $3.75 per 1M input/output tokens until 2026-12-31; **$1.50 / $7.50 from 2027-01-01** | Paid tier: content not used to improve products | [pricing](https://ai.google.dev/gemini-api/docs/pricing). Free-tier rate limits are only shown in AI Studio [UNVERIFIED] |
| **Claude Sonnet 5.5** | T1/T2 candidate, meaning-check | [UNVERIFIED: measured] | Small free credits for new users | $2 / $10 per 1M input/output tokens | — | [pricing](https://platform.claude.com/docs/en/about-claude/pricing) |
| Claude Haiku 4.5 | Cheaper fallback | [UNVERIFIED] | as above | $1 / $5 per 1M | — | as above |
| Sarvam Mayura / Sarvam-Translate | Optional second baseline (Indic-specialised) | Yes | ₹100 shared credits | ₹0.005 per character (pay-as-you-go) | See the Sarvam conflict above | [models](https://docs.sarvam.ai/api-reference-docs/getting-started/models), [pricing](https://www.sarvam.ai/api-pricing) |

### Tamil speech synthesis and voice cloning

| Candidate | Tamil | Cloning | Delete API | Free tier | Price | Consent / training terms | Source |
|---|---|---|---|---|---|---|---|
| **Google Chirp 3 HD** (stock) `ta-IN-Chirp3-HD-*` | **Yes, GA** | Instant Custom Voice supports `ta-IN` but is **allowlist-only**, so excluded | — | 1M chars/month | $30 per 1M chars (figures from search results on the official pricing page) | — | [Chirp 3 HD](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd), [ICV](https://docs.cloud.google.com/text-to-speech/docs/chirp3-instant-custom-voice), [pricing](https://cloud.google.com/text-to-speech/pricing) |
| **Sarvam Bulbul v3** (stock) | **Yes** (`ta-IN`) | — | — | ₹100 credits | ₹3 per 1,000 chars. Pace 0.5×–2.0×. Max 2,500 chars per request. | See the conflict above | [Bulbul](https://docs.sarvam.ai/api/getting-started/models/bulbul), [pricing](https://www.sarvam.ai/api-pricing) |
| **Sarvam voice cloning** | **Yes** (`ta-IN` in the cloning list; any supported reference language can drive any target) | Yes; saved `voice_id` | **Delete Voice** listed in the API reference (from search results; confirm in the spike) | ₹100 credits | ₹30 per 10K chars **[UNVERIFIED: from a search summary, confirm on the dashboard]**. Limit 10 req/min sustained (Starter). | **A consent acknowledgement is mandatory** before saving a clone. You must have rights to the voice. | [languages](https://docs.sarvam.ai/api/api-guides-tutorials/voice-cloning/supported-languages), [reference audio](https://docs.sarvam.ai/api/api-guides-tutorials/voice-cloning/how-to/prepare-reference-audio), [cloning](https://docs.sarvam.ai/creative-voice-cloning), [limits](https://docs.sarvam.ai/api-reference-docs/getting-started/pricing) |
| **ElevenLabs** IVC | Tamil in **Multilingual v2, Flash v2.5, Eleven v4**; **not listed for Eleven v3** | IVC from the **Starter** plan; **not on Free** | `DELETE /v1/voices/{voice_id}` | Free: 10K credits, no IVC, no commercial licence | Starter **$6/month** (the page also shows a $1 first-month figure; confirm at purchase), 30K credits. API: v2 $0.08 per 1K chars; v4 $0.022 per 1K chars (temporary discount). Credits consumed per character per model **[UNVERIFIED]**. | Prohibited-use policy forbids cloning "without consent or legal right". A training opt-out toggle exists. Zero Retention Mode is enterprise-only. | [models](https://elevenlabs.io/docs/models), [pricing](https://elevenlabs.io/pricing), [API pricing](https://elevenlabs.io/pricing/api), [delete](https://elevenlabs.io/docs/api-reference/voices/delete), [use policy](https://elevenlabs.io/use-policy), [data use](https://elevenlabs.io/docs/help-center/legal/is-my-data-used-to-improve-eleven-labs-ai-models) |
| Azure Speech | Tamil TTS voices **[UNVERIFIED]** (not in the fetched page) | Personal Voice is limited access, so excluded | — | 0.5M chars/month | — | — | [pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/) |

### Hard gates (any failure excludes the candidate; recorded with the reason)

| Gate | Check |
|---|---|
| G1 Language | Official documentation lists English (ASR) or Tamil (translation, TTS, cloning) |
| G2 Training | Our account settings or tier stop training on our data (paid tier, opt-out applied, or a contractual statement) |
| G3 Access | Usable without an allowlist or sales contact (excludes Google ICV and Azure Personal Voice) |
| G4 Deletion | Voice profiles can be deleted through the API (cloning only) |
| G5 Cost | Fits the ₹1,500 spike cap and a realistic ₹2,000/month MVP budget (§7) |

**Comparison slots:**

| Stage | Slots |
|---|---|
| ASR | **A1** Groq whisper-large-v3 · **A2** Sarvam Saaras v4 |
| Translation | **T0** Google NMT · **T1** LLM without context · **T2** LLM with full textual context. T1/T2 are run with **Gemini 3.8 Flash (paid)** and **Claude Sonnet 5.5**. |
| Meaning-check (AI flags) | Same-family checker vs. other-family checker (e.g. Gemini translation checked by Claude, and vice versa) |
| Stock TTS | **V0a** Google Chirp 3 HD `ta-IN` · **V0b** Sarvam Bulbul v3 |
| Cloned voice | **V1** Sarvam voice cloning · **V2** ElevenLabs IVC (Starter) |

## 4. Measurements

All spike scripts live in `spike/`. They are throwaway, never imported by the app, and committed only for reproducibility. Each run records the provider, model and version, prompt text and version, parameters, date, hardware and usage units. Each measurement is run 3 times where timing matters; the median and maximum are reported.

### M1: Transcription accuracy → decides **ADR 0017**

| | |
|---|---|
| **Metrics** | **WER** against the reference transcript (normalisation fixed in advance: lowercase, strip punctuation, numbers normalised to digits); **critical-token error rate** (% of the script's numbers, units and glossary terms transcribed wrongly); **boundary error** (mean absolute ms between ASR segment boundaries and the hand-marked ones); **real-time factor**. |
| **Method** | A1 and A2 on the same audio (mono, 16 kHz). Scored with a standard WER library (e.g. `jiwer`). |

### M2: Translation quality, rated by R1 and R2 → decides **ADR 0016** (and the AI-flag design in ADR 0008)

| | |
|---|---|
| **Input** | The **reference transcript**, so ASR errors don't contaminate the comparison |
| **Systems** | T0; T1 and T2 × 2 LLMs (5 outputs per segment) |
| **Human rating (main)** | R1 and R2 **independently** label every output segment, blind to the system (shuffled order, IDs hidden). They use MQM-style categories (accuracy, fluency, terminology, style, locale) and severities (critical / major / minor). Score = weighted error points per 100 source words (minor 1, major 5, critical 10). |
| **Pairwise preference** | For each segment, R1 and R2 independently choose the better of T2 vs. T0 and T2 vs. T1, or "equal". |
| **Calibration** | R1 and R2 rate 5 practice segments together beforehand (not counted) using a short written guideline. |
| **Agreement between the 2 raters** | Cohen's κ on the per-segment binary label "has a major or critical error"; weighted κ on the highest severity; κ on the pairwise choices; plus raw % agreement. Reported **before** discussing disagreements. Then R1 and R2 discuss each disagreement and the agreed label is used for the decision. |
| **Automatic (supporting only)** | chrF against R1's reference (e.g. `sacreBLEU`). A learned metric (e.g. COMET) only if its model documentation covers Tamil [UNVERIFIED]; otherwise left out and noted. |
| **Caveat** | About 30 segments and 2 raters: **directional only**. |

### M3: Rule-check and AI-flag catch rate on seeded errors → validates **ADR 0008** for Tamil; feeds ADR 0016

| | |
|---|---|
| **Method** | Run a throwaway prototype of the hard checks (Tamil digit, numeral and number-word normaliser; unit lexicon; glossary accepted forms) and both meaning-check configurations on the 20 seeded errors and the clean segments. |
| **Metrics** | **Hard-check catch rate** on number, unit and term errors (counting `UNVERIFIABLE` as caught-for-review, reported separately); **hard-check false-alarm rate** on clean segments; **AI-flag catch rate** on the 10 reversal and omission errors; **AI-flag false-alarm rate**; whether the other-family checker beats the same-family one. |
| **Decides** | The realistic scope of the Tamil normaliser and lexicon for S1, and which model runs the meaning-check |

### M4: Tamil TTS quality → decides **ADR 0018** and **ADR 0015** (is cloned voice viable?)

| | |
|---|---|
| **Input** | The **same fixed Tamil text** (R1's reference) for every system |
| **Systems** | V0a, V0b, V1, V2 |
| **Naturalness** | R1 and R2 (plus any other Tamil-speaking listeners; report *n*) rate each system 1–5, blind to the system. With a small *n* this is indicative only. |
| **Critical-content pronunciation** | R1 and R2 mark each number, unit and glossary term: correct / wrong / unclear. Digits are tested both as digits and as words, which decides whether ADR 0008's separate speech script is needed. |
| **Intelligibility** | ASR round-trip: transcribe the synthesised Tamil with one fixed Tamil-capable ASR (e.g. Saaras v4) and compute the character error rate against the input. **The same ASR is used for every system**, so this is a relative measure only. |
| **Speaker similarity (cloning only)** | Objective: cosine similarity of speaker-verification embeddings (e.g. a publicly available ECAPA-TDNN model running on CPU [UNVERIFIED that it runs acceptably on our laptop]), original vs. synthesised, with **V0 as the control**. Subjective: listeners who know the speaker answer "same person?" 1–5. |

### M5: Timing fit → feeds ADRs 0016 and 0018

| | |
|---|---|
| **Metric** | Synthesised duration ÷ source slot duration, per segment. Reported as a distribution and as the % of segments within ±15% (an **assumed working threshold**, to be revisited). |
| **Method** | T2 output **without vs. with** the length constraint in the prompt, synthesised by the best stock voice at 1.0× and with bounded pace adjustment (at most ±15%). |

### M6: Latency → feeds ADR 0003 (job sizing) and ADR 0006 (time-to-stop bound); demo planning (ADR 0012)

| | |
|---|---|
| **Metrics** | Wall-clock time per stage per minute of source; **longest single synthesis call** (this is the upper bound on how long revocation takes to stop a job); total time to synthesise a 30-segment scene **including rate-limit waits** (especially Sarvam cloning at 10 requests/min). |
| **Method** | 3 runs; median and max; first (cold) call reported separately; network and date recorded. |

### M7: Cost per video minute → decides ADRs 0016–0018 and MVP budget feasibility

| | |
|---|---|
| **Metric** | ₹ per minute of source video, per stage and in total, for each candidate combination. Regeneration overhead is reported separately. |
| **Method** | Metered units from each provider's usage dashboard or API (audio seconds, tokens, characters, credits) × the price on the spike date (price-page URL and date recorded) × ₹100/USD (a conservative planning rate; the observed rate was about ₹96.3 on 2026-10-04). Compared with the estimates in §7. |

### M8: Provider data handling (document check, not a measurement) → gates G2–G4

Confirm in writing or in account settings:
- training opt-out status (Sarvam: resolve the conflict; ElevenLabs: toggle; Gemini: paid tier; Groq: ZDR);
- retention periods;
- that the delete-voice API works: create a voice, delete it, then confirm that listing voices no longer shows it.

## 5. Decision rules (fixed before seeing results)

These rules are written now, before any results exist, so that the results can't be fitted to a preferred answer afterwards.

1. **Gates first.** Any failure of G1–G5 excludes the candidate.
2. **ASR (ADR 0017):** lowest critical-token error rate. If within 2 percentage points, lower WER. If still tied, cheaper, then the clearer no-training terms.
3. **Translation (ADR 0016):** fewest weighted MQM points (agreed labels). Ties are broken by hard-check pass rate, then cost. If T2 does not beat T0, the result is recorded honestly. T2 is still built (it carries the rationale and audience profile), and the S4 ablation decides the claim.
4. **Cloned voice (ADR 0015 / 0018):** `CLONED_VOICE` enters the MVP only if a cloning candidate passes G1–G5 **and**:
   - its critical-content pronunciation errors are no more than the best stock voice's **plus 1**;
   - its naturalness median is at least 3/5;
   - its objective similarity is above the V0 control;
   - its subjective "same person?" median is at least 3/5.

   These thresholds are [PROPOSED]; confirm or change them before the spike. Otherwise the MVP ships `STOCK_VOICE` only, and you are told before ADR 0015 is finalised.
5. **Stock voice (ADR 0018):** fewest critical-content pronunciation errors, then naturalness, then cost.
6. **Meaning-check:** the configuration with the highest AI-flag catch rate, provided its false-alarm rate is ≤ 30% [PROPOSED].
7. **Budget:** if the cheapest acceptable combination is projected to exceed ₹1,800/month at the planned development volume (§7), escalate to you.

## 6. Outputs

- `docs/EVALUATION.md` (created at this point): metric, definition, TARGET (set from the spike), **MEASURED RESULT** (labelled "spike, 1 clip, n = …"), and method.
- A spike results section: excluded candidates with reasons, measured values, and the outcome of each decision rule.
- Updated ADRs 0015–0018 (from "Pending spike results" to "Proposed"), citing the measured values, for your approval.
- `spike/` scripts. No media and no raw transcripts are committed.

## 7. Cost estimate

**ESTIMATE only: assumptions, not measurements.** Planning rate: ₹100/USD (conservative).

Assumptions:
- 2-minute clip; about 1,800 English characters; about **3,500 Tamil characters** of output (assumed and deliberately generous, because Tamil script uses more characters; measured in M7); 30 segments.
- LLM token use per model:
  - T2: about 2,000 input + 400 output tokens per segment;
  - T1: about 600 input + 400 output;
  - meaning-check: about 800 input + 150 output per check, over about 100 checks;
  - all × 3 runs, giving about **474K input and 117K output tokens**;
  - **+30%** for the newer Claude tokenizer, and **+50% overall margin** on all LLM costs.
- TTS: 5 passes of 3,500 characters per system, about **17,500 characters per system**.

| Item | Calculation | Estimate |
|---|---|---|
| ASR: Groq (6 min audio) | free tier | ₹0 |
| ASR: Sarvam Saaras (6 min) | 0.1 h × ₹30 | ₹3 |
| T0 Google NMT (5.4K chars) | free tier | ₹0 |
| Optional Sarvam Mayura (5.4K chars) | × ₹0.005 | ₹27 |
| Gemini 3.8 Flash paid | 0.474M × $0.75 + 0.117M × $3.75 ≈ $0.80 | ₹80 |
| Claude Sonnet 5.5 | (0.474M × $2 + 0.117M × $10) × 1.3 ≈ $2.76 | ₹276 |
| LLM margin (+50% of the two lines above) | | ₹178 |
| Stock TTS: Google Chirp 3 HD | 17.5K ≪ 1M free | ₹0 |
| Stock TTS: Sarvam Bulbul v3 | 17.5K × ₹3/1K | ₹53 |
| Cloning: Sarvam | 17.5K × ₹3/1K (price [UNVERIFIED]) | ₹53 |
| Cloning: ElevenLabs Starter, 1 month | $6 (conservative; covers 30K credits) | ₹600 |
| **Subtotal** | | **₹1,270** |
| Sarvam signup credits | | −₹100 |
| **Estimated spike total** | | **≈ ₹1,170** |
| **Hard cap** | | **₹1,500** |

The estimate is below the ₹1,500 cap, which is below the ₹2,000/month budget. **The cap is enforced by checking the provider dashboards after each stage**; the in-app cap (ADR 0005) doesn't exist yet.

**Not included:** Google Cloud and Gemini paid usage need a billing account. Whether free-tier credits apply automatically is [UNVERIFIED].

**Monthly running cost after the spike (estimate for planning, to be replaced by M7):** per minute of video, transcription ≈ ₹0.2, LLM translation and checking ≈ ₹8 (Gemini) to ₹25 (Claude), Tamil cloned speech ≈ ₹5 (Sarvam). That is roughly **₹15–30 per video minute** before regenerations; assuming two regenerations per minute on average, about ₹45–90. Within ₹1,800/month, that allows roughly **20–120 video minutes per month** of development and demo processing, which is enough for a 3–5 clip test set. If ElevenLabs is chosen, its $6 subscription is a fixed monthly cost on top.

## 8. Time box and risks

**Time box:** 5 working days, split across 2 people [PROPOSED]. One person prepares the material and runs ASR/TTS; the other runs translation and the checks. R1 and R2 need about 3–4 hours each for rating.

| Risk | Mitigation |
|---|---|
| The training opt-out for Sarvam can't be confirmed | Sarvam fails G2; ElevenLabs/Google become the candidates. |
| No cloning candidate meets rule 4 for Tamil | Stock voice in the MVP; the identity claim is narrowed; escalate. |
| Prices differ at purchase time (e.g. ElevenLabs Starter $1 vs. $6) | The estimate uses the higher figure; the cap still holds. |
| Gemini price doubles on 2027-01-01 (inside the 5-month window) | The cost-per-minute projection in M7 uses the 2027 price. |
| Rater fatigue or disagreement | Calibration round, short guideline, κ reported honestly. |
| One clip is not representative | Stated in every result; the full evaluation uses 3–5 clips. |
