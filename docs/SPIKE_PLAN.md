# HyperLocalize: Technical Spike Plan (English → Tamil, zero budget)

| | |
|---|---|
| **Date** | 2026-10-05 (revision 3: zero budget) |
| **Status** | PLAN ONLY. **Not run.** Needs your approval. |
| **Purpose** | Produce measured evidence to decide ADRs 0015–0019 ("Pending spike results"), to check ADR 0008's limits for Tamil, and to choose the demo plan (§6) |
| **Language pair** | English (`en`) → Tamil (`ta-IN`) |
| **Budget** | **₹0.** Free tiers and open-source models only. No billing-enabled accounts (ADR 0005). |
| **Compute** | Team laptop CPU (specs recorded at the start, see P8) + Kaggle Notebooks GPU (free, about 30 h/week) |
| **Raters** | 2 bilingual English–Tamil raters, R1 and R2 |
| **Terms** | `docs/THIRD_PARTY_TERMS.md`, including Gemini free-tier training and human review, and IndicF5 treated as non-commercial |

All results are **MEASURED RESULTS on one clip** (n = 1 clip, about 30 segments). They are directional evidence for choosing between options, not quality claims. Quality claims come from the full evaluation (slice S4, 3–5 clips).

---

## 1. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| P1 | Language pair, raters, data policy | Done (Q3, Q6, Q7) |
| P2 | Budget rule | Done: zero spend (Q4, revised) |
| P3 | Hugging Face account; access accepted for the **gated** models IndicF5, IndicTrans2 and Indic Parler-TTS | To do |
| P4 | **Kaggle account with phone verification** (required for GPU and internet) | To do. A blocking risk if verification fails (§9). |
| P5 | Gemini API key from AI Studio on a project **with no Cloud Billing** (so it stays on the free tier); Groq free account (no card) with **Zero Data Retention on** | To do |
| P6 | Signed consent from each recorded team member naming the processors: **Groq** (transcription audio), **Kaggle** (reference clip, cloned output), **Google Gemini free tier** (script text only; may be used for training and seen by human reviewers) | To do |
| P7 | Your approval of this plan and the proposed decision thresholds (§5) | **Waiting** |
| P8 | **Laptop specs:** CPU model and cores, RAM, OS. Recorded in the results; every CPU number depends on them. | To do. Please tell me which laptop will run the demo. |

## 2. Test material

The same design as before: a **90–120 s** health-information clip (proposed topic: safe use of oral rehydration salts [PROPOSED]), scripted to contain:
- at least 10 numbers, 5 units, 5 glossary terms, 5 negated instructions, 2 idioms;
- a reference transcript and hand-marked segment boundaries;
- **R1's reference translation**, written before any system output is seen, and checked by R2;
- a glossary with accepted inflected Tamil forms, and a Tamil unit lexicon (from R1/R2);
- the **seeded-error set** (20 rule-checkable errors + 10 reversal/omission errors).

For IndicF5, each consenting speaker records:
- **(a)** an English reference clip (10–15 s);
- **(b)** a Tamil reference clip (10–15 s, read from a short Tamil text).

Each comes with its exact transcript. This tests whether cross-lingual prompting loses the speaker's identity.

**Data handling.**
- Media is never committed to git.
- A log records each upload (Groq, Kaggle).
- Every Kaggle dataset and kernel is deleted after the spike (`kaggle datasets delete`, `kaggle kernels delete`), and the deletion is recorded.

## 3. Candidates (checked 2026-10-05; details and sources in `THIRD_PARTY_TERMS.md`)

| Stage | Slot | Candidate | Runtime | Licence / terms |
|---|---|---|---|---|
| Transcription | **A1** | Groq `whisper-large-v3` | Hosted, free plan | No training; ZDR on |
| | **A2** | faster-whisper `small` and `medium`, int8 | Laptop CPU | MIT |
| Translation | **T0** | IndicTrans2 En→Indic dist-200M (context-free baseline) | Laptop CPU | MIT, gated |
| | **T1 / T2** | Gemini Flash, free tier: without context / with full context | Hosted | **Free tier: training + human review**; script text only |
| | **T1 / T2** | Groq `llama-3.3-70b-versatile` and `openai/gpt-oss-120b`: without / with context | Hosted, free plan | No training |
| Meaning-check | **C-same / C-other** | Checker from the same vs. a different model family as the translator | Hosted | as above |
| Stock voice | **V0a** | MMS-TTS Tamil | Laptop CPU | CC-BY-NC-4.0 |
| | **V0b** | Indic Parler-TTS (speaker "Jaya") | Laptop CPU (and Kaggle if CPU is too slow) | Apache-2.0, gated |
| | **V0c** (optional) | ElevenLabs free plan, Tamil-capable model | Hosted | Non-commercial; attribution |
| Cloned voice | **V1-cpu** | IndicF5 | Laptop CPU | Treated as non-commercial; gated |
| | **V1-gpu** | IndicF5 | Kaggle GPU batch | same |

**Hard gates** (any failure excludes the candidate):
- **G1 language:** documented support.
- **G2 data terms:** compatible with the data it would receive.
- **G3 access:** obtainable free, without an allowlist.
- **G4 zero spend:** no payment method needed.
- **G5 runnable:** fits in laptop RAM, or within a 12-hour Kaggle session.

## 4. Measurements

All spike scripts and notebooks live in `spike/` and `spike/kaggle/`. They are throwaway, never imported by the app, and committed only for reproducibility. Each run records the model and version, prompt or version, parameters, seed, date, hardware, and timings. Timing runs are repeated 3 times; the median and maximum are reported, plus the first (cold) run separately.

### M1: Transcription accuracy and speed → **ADR 0017**

- **Metrics:** WER (with normalisation rules fixed in advance); **critical-token error rate** (numbers, units, glossary terms); segment-boundary error (ms); **real-time factor** (processing time ÷ audio duration); peak RAM for A2.
- **Method:** A1 and A2 (small and medium) on the same 16 kHz mono audio.

### M2: Translation quality, rated by R1 and R2 → **ADR 0016**

- **Input:** the reference transcript, so ASR errors don't contaminate the comparison.
- **Systems:** T0 + T1/T2 for each hosted LLM (5 outputs per segment).
- **Human rating:** R1 and R2 rate independently and **blind** (shuffled, system hidden), using MQM-style categories and severities (minor 1, major 5, critical 10 points per 100 source words). Then a blind pairwise preference: T2 vs. T0 and T2 vs. T1.
- **Calibration:** 5 practice segments, not counted.
- **Agreement between the two raters:** Cohen's κ on "has a major or critical error"; weighted κ on the highest severity; κ on the pairwise choices; raw % agreement. Reported **before** the raters discuss disagreements; the agreed labels after discussion are used for decisions.
- **Automatic (supporting only):** chrF against R1's reference. COMET only if its model documentation covers Tamil [UNVERIFIED].
- **Also recorded:** requests and tokens used per video minute (for M7) and latency.

### M3: Rule-check and AI-flag catch rate on seeded errors → **ADR 0008**, meaning-check part of **ADR 0016**

- **Method:** run a throwaway prototype of the hard checks (Tamil digits ௦–௯, the numerals ௰ ௱ ௲, the number-word lexicon, unit lexicon, glossary accepted forms), plus both meaning-check configurations, on the 30 seeded errors and the clean segments.
- **Metrics:**
  - hard-check catch rate, by error type (Western digits / Tamil digits / Tamil number words / units / terms), with `UNVERIFIABLE` reported separately;
  - hard-check false-alarm rate on clean segments;
  - AI-flag catch rate on reversals and omissions, and its false-alarm rate;
  - same-family vs. other-family checker.

### M4: Tamil TTS quality → **ADR 0018**, **ADR 0015**

- **Input:** the same fixed Tamil text (R1's reference) for every system.
- **Systems:** V0a, V0b, (V0c), V1 with the English reference clip, V1 with the Tamil reference clip.
- **Naturalness:** R1, R2 and any other Tamil listeners rate 1–5, blind to the system (report *n*).
- **Critical-content pronunciation:** R1 and R2 mark each number, unit and glossary term correct / wrong / unclear, tested **both with digits and with numbers written as words**. This decides whether ADR 0008's separate speech script is needed.
- **Intelligibility (relative):** transcribe the synthesised Tamil with one fixed Whisper model and compute the character error rate against the input. The same ASR is used for all systems.
- **Speaker similarity (cloned voice only):** cosine similarity of speaker-verification embeddings (an open ECAPA-TDNN model run on CPU [UNVERIFIED that it runs acceptably on our laptop]), original vs. synthesised, with V0 as the control. Plus "same person?" ratings (1–5) from listeners who know the speaker.

### M5: Timing fit → **ADRs 0016, 0018**

- **Metric:** synthesised duration ÷ source slot duration, per segment; reported as a distribution and the % within ±15% (an assumed working threshold).
- **Method:** T2 output without vs. with the length constraint in the prompt, through the best stock voice at 1.0× speed and with a bounded tempo adjustment of ±15% (ffmpeg `atempo`).

### M6: Speed: **IndicF5 on CPU vs. Kaggle GPU** (requirement 3) → **ADRs 0018, 0019, 0012** and the demo plan (§6)

The same 10 segments (a mix of short and long, about 3–8 s of speech each), the same reference clip, and the **same seed** on both runtimes.

| Metric | Laptop CPU | Kaggle GPU |
|---|---|---|
| Model load time (cold) | ✓ | ✓ |
| **Per-segment synthesis time** (median and max) | ✓ | ✓ |
| **Real-time factor** (synthesis time ÷ audio duration) | ✓ | ✓ |
| Peak RAM (and GPU memory on Kaggle) | ✓ | ✓ |
| **End-to-end batch time** for a 30-segment scene: dataset upload → kernel queue and start → model load → synthesis → output download → import | n/a | ✓ |
| **GPU-hours used per minute of output audio** → projected **video minutes per week** within the free quota | n/a | ✓ |
| Laptop responsiveness while synthesising (does the web UI stay usable?) | ✓ (observed) | n/a |

Also measured on CPU: MMS-TTS and Indic Parler-TTS per-segment time and RTF; IndicTrans2 time per segment.

**Equivalence check:** R1 and R2 do a blind A/B comparison of 3 CPU vs. GPU outputs (same seed). If they're audibly different, both are rated in M4.

### M7: Free-quota capacity → **ADR 0005** (chain order and quota warnings)

- **Metrics:** requests, tokens and audio-seconds consumed per video minute at each hosted stage. Free-tier limits **as observed** (Gemini's limits are only shown in AI Studio; Groq's are published). Result: projected **video minutes per day** before each quota runs out, and which stage hits its limit first.

### M8: Zero-spend confirmation → **ADR 0005**

Confirm that no account used has billing enabled, and record the screenshots or settings. Expected cost: **₹0**.

### M9: Revocation mechanics → **ADR 0006**, **ADR 0019**

- **Local:** start a 10-segment IndicF5 CPU job and revoke mid-segment. Measure **time from the revocation commit to the subprocess being killed**; confirm no output was saved and temp files are gone.
- **Kaggle:** dispatch a batch and, while it runs, run `kaggle kernels delete` and `kaggle datasets delete`. Then record:
  - (a) whether the kernel stops or completes (check its status and the GPU quota used);
  - (b) whether `kaggle datasets list` and `kaggle kernels list` still show them;
  - (c) that a late import attempt is refused by CP5. This is a design test; the CP5 code itself is built in S3.

## 5. Decision rules (fixed before seeing results)

These rules are written now, before any results exist, so that the results can't be fitted to a preferred answer afterwards.

1. **Gates first.** Any failure of G1–G5 excludes the candidate.
2. **ASR (ADR 0017):** lowest critical-token error rate. If within 2 percentage points, prefer the **local** model (no quota). Otherwise the lower WER.
3. **Translation (ADR 0016):** fewest weighted MQM points (agreed labels); ties broken by hard-check pass rate, then the better data terms (no-training preferred). If T2 doesn't beat T0, the result is recorded honestly; T2 is still built, and the S4 ablation decides the claim. The next-best free LLM becomes the chain alternative, and IndicTrans2 is always the last resort.
4. **Cloned voice in the MVP (ADR 0015):** IndicF5 qualifies only if all of these hold [PROPOSED thresholds; confirm before the spike]:
   - critical-content pronunciation errors ≤ the best stock voice's **+ 1**;
   - naturalness median ≥ 3/5;
   - objective similarity above the V0 control;
   - "same person?" median ≥ 3/5.

   The better of the English or Tamil reference clip is used. Otherwise the MVP uses stock voice only, and you are told first.
5. **Stock voice (ADR 0018):** fewest critical-content pronunciation errors, then naturalness, then CPU speed.
6. **Runtime for cloned voice (ADRs 0018, 0019):**
   - **CPU is "fast enough for live use"** if the median per-segment IndicF5 time is ≤ 20 s, a 3-segment scene takes ≤ 60 s, and peak RAM stays ≤ 70% of laptop RAM with the app running [PROPOSED].
   - **Kaggle is adopted** for pre-rendering if a 30-segment scene completes end to end in ≤ 30 min and the projected free capacity is ≥ 10 video minutes per week [PROPOSED].
7. **Meaning-check:** the configuration with the highest AI-flag catch rate, provided its false-alarm rate is ≤ 30% [PROPOSED].

## 6. Demo plan (chosen by rule 6)

| Situation | Demo plan |
|---|---|
| **CPU fast enough** (rule 6 met) | **Plan A:** everything live on the laptop, including a cloned-voice regeneration of one short scene. Kaggle is optional. |
| **CPU too slow, Kaggle OK** | **Plan B** (below) |
| **CPU too slow and Kaggle unavailable** (no phone verification, or quota gone) | **Plan C:** cloned-voice previews are rendered on CPU **overnight** before the demo (slow is fine offline). Live work uses the stock voice. Revocation is still demonstrated on a local CPU job. |
| **Cloned voice fails rule 4** | Stock voice only. Consent governance is demonstrated on the speaker's recorded voice and the identity record. The identity claim is narrowed. |

**Plan B, step by step.**

| When | What |
|---|---|
| T-3 days | Run Kaggle batches for every scene of the demo project. Import through the consent checks. Previews are ready and have been reviewed. |
| T-1 day | Run `check_providers`: free quotas, remaining Kaggle GPU hours, the HF models cached locally. Rehearse. Record the backup screen recording. |
| Live: review | Open the real, pre-rendered previews and say so: "these cloned-voice previews were rendered on a free Kaggle GPU yesterday, through the same consent checks." |
| Live: regenerate | Request changes on one scene → regenerate **with the stock voice on CPU** (fast) so the full loop is visible live. Also **dispatch** a cloned-voice regeneration to Kaggle, show its `DISPATCHED` state, and show the result at the end only if it has arrived. |
| Live: revoke | Start a **local CPU cloned-voice job** on a multi-segment scene. Because it's slow, it's reliably mid-job. The Identity Owner revokes, and the audience sees: subprocess killed within seconds, job `CANCELLED (consent revoked)`, the earlier Kaggle-rendered previews **quarantined**, the approval invalidated, the stock-voice fallback queued, Kaggle copies deleted (or "deletion pending"), and the audit trail. |
| Live: approve and export | Approve the fallback version; export; show the evidence manifest, including the audit chain head and the non-commercial licence notice. |
| If something fails | The recorded run, announced as a recording. |

## 7. Outputs

- `docs/EVALUATION.md` (created at this point): each metric with its definition, TARGET (set from the spike), **MEASURED RESULT** ("spike, 1 clip, n = …") and method.
- A spike results section: excluded candidates with reasons, measured values, the outcome of each rule, and the **chosen demo plan**.
- ADRs 0015–0019 updated from "Pending spike results" to "Proposed", citing the measured values.
- `spike/` scripts and Kaggle notebooks. No media and no raw transcripts are committed.

## 8. Cost

| Item | Cost |
|---|---|
| Groq free plan, Gemini free tier (no billing), Hugging Face models, Kaggle free GPU, local CPU | **₹0** |
| Optional ElevenLabs free plan (V0c) | ₹0 |
| **Total** | **₹0** (confirmed in M8) |

The real "costs" are quota and time:
- Kaggle GPU hours, roughly a few hours of the weekly quota for the spike. This is an estimate; the actual figure comes from M6.
- Free LLM requests, small for one clip.
- Team time: about 5 working days across 2 people [PROPOSED], plus 3–4 hours of rating each for R1 and R2.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Kaggle phone verification fails or is delayed (Kaggle's own forums report problems) | Start P4 first. If it fails: Plan C (overnight CPU rendering), and ADR 0019 is dropped. |
| Gated model access is delayed | Request access on day 0; MMS-TTS (not gated) keeps the stock voice working. |
| IndicF5 on CPU needs too much RAM for the laptop | Measured in M6. Kaggle or Plan C rendering; run synthesis only when the app is otherwise idle. |
| Free-tier limits change during the 5 months | Provider chains (ADR 0005); quota warnings; IndicTrans2 and faster-whisper are local and have no quota. |
| Gemini free-tier terms (training, human review) | Script text only; never audio or third-party content; disclosed in the consent form. |
| IndicF5 licence ambiguity | Treated as non-commercial; academic scope stated everywhere. |
| One clip is not representative | Stated in every result; full evaluation on 3–5 clips. |
