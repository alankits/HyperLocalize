# HyperLocalize: Technical Spike Plan (English → Tamil, zero budget)

| | |
|---|---|
| **Date** | 2026-10-05 (revision 4: independent-review fixes) |
| **Status** | **Approved 2026-10-05** (plan and §5 thresholds). **Not run**: waiting on prerequisites P3–P6 and P8. |
| **Purpose** | Produce measured evidence to decide ADRs 0015–0019 ("Pending spike results"), to check ADR 0008's limits for Tamil, and to choose the demo plan (§6) |
| **Language pair** | English (`en`) → Tamil (`ta-IN`) |
| **Budget** | **₹0.** Free tiers and open-source models only; no billing-enabled accounts (ADR 0005) |
| **Compute** | The **demo laptop**, running the Docker Compose stack (specs recorded, see P8) + Kaggle GPU (only if rule 6 says it's needed) |
| **Raters** | 2 bilingual English–Tamil raters, R1 and R2 |
| **Terms** | `docs/THIRD_PARTY_TERMS.md` |

All results are **MEASURED RESULTS on one clip** (n = 1 clip, about 30 segments): **directional evidence** for choosing between options, not quality claims. Quality claims come from the full evaluation (slice S4, 3–5 clips).

---

## 1. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| P1 | Language pair, raters, data policy | Done |
| P2 | Budget rule | Done: zero spend |
| P3 | Hugging Face access accepted for the gated models IndicF5, IndicTrans2 and Indic Parler-TTS | **Pending.** Access requested (user, 2026-10-05). Approval is not assumed until confirmed for each model. |
| P4 | Kaggle account with **phone verification** (needed only if rule 6 calls for Kaggle; start early anyway) | Done (phone verified; reported by user 2026-10-05) |
| P5 | Gemini API key from AI Studio on a project **with no Cloud Billing**; Groq free account with **Zero Data Retention on** | **Partly done** (reported by user 2026-10-05). Gemini key created on a project with no billing; not yet in `.env` and not shared. Groq: Inference APIs ZDR available and enabled. **Still to check:** whether ZDR covers the speech-to-text endpoint used by slot A2 [UNVERIFIED]. **No audio is sent to Groq** until this is checked and consent 3.3 is signed. |
| P6 | Signed consent (`docs/spike/CONSENT_FORM.md`) from each recorded speaker (team member or volunteer), with each permission ticked separately: 3.0 recording and local processing; 3.1 `voice_synthesis`; 3.2 `remote_voice_processing` (Kaggle, only if rule 6 calls for it); 3.3 `external_transcription` (Groq, Speaker A only, needed only for slot A2); 3.4 listening tests; 3.5 voice comparison score; 3.6 clone as a comparison sample; plus the §4 disclosure that the **Gemini free tier receives script text** (may be used for training and seen by human reviewers). **At least 2 speakers** are needed for the M4 similarity control. *(Aligned with the consent form 2026-10-06, round-2 fix P9.)* | To do |
| P7 | Your approval of this plan and the decision thresholds (§5) | Done (2026-10-05) |
| P8 | **Demo laptop specs:** CPU model and cores, RAM, OS, and the Docker memory limit | **Done** (confirmed by user 2026-10-05): Intel Core i5-13450HX, 10 cores / 16 threads, 14 GiB RAM, x86_64, Linux kernel 7.0.0-34-generic. Docker memory limit: 8 GB (see P9). **Ubuntu release: Ubuntu 26.04.1 LTS** (read with `lsb_release -d` on this laptop, 2026-10-06). P8 done. |
| P9 | **Docker Engine and Docker Compose installed on the demo laptop, and the Docker memory limit chosen.** On Linux, Docker sets no memory limit by default, and ADR 0012 doesn't set one, so the limit is **your decision**, written in the Compose file. *(Added 2026-10-05.)* | **Partly done.** Memory limit chosen: **8 GB** (user, 2026-10-05), written in the Compose file as `8g` (Docker reads this as 8 GiB), leaving about 6 GiB of the laptop's 14 GiB for the host. Rule 6a's 70% line is therefore about 5.6 GiB. **Docker is not installed yet. Blocks:** M6 CPU timings (run inside Compose, §4) and rule 6a (peak RAM ≤ 70% of the limit), so it also blocks the demo-plan choice. |

## 2. Test material

- A **90–120 s** health-information clip (topic: safe use of oral rehydration salts [CONFIRMED, Q17]; script: `docs/spike/TEST_SCRIPT.md`), scripted to contain at least 10 numbers, 5 units, 5 glossary terms, 5 negated instructions and 2 idioms.
- A reference transcript and hand-marked segment boundaries.
- **R1's reference translation**, written before any system output is seen, and checked by R2. Known bias: R1 also rates, and may favour outputs that resemble their own reference. This is stated; chrF is supporting evidence only.
- A glossary with accepted inflected Tamil forms, and a Tamil unit lexicon (from R1/R2).
- **IndicF5 reference clips:** each of the 2 consenting speakers records an English clip and a Tamil clip (8–11 s each, with exact transcripts; matches `TEST_SCRIPT.md` §3 and the consent form, corrected 2026-10-05).
- **Seeded-error set,** written by **R2 only after the check rules are frozen** *(changed after review, to avoid optimistic catch rates)*. Neither R2 nor R1 writes check code.
  - 20 errors that the rule checks should catch: wrong Western-digit number ×3, wrong Tamil-digit number ×2, number written as a Tamil word ×3 (expected `UNVERIFIABLE`), wrong or missing unit ×4, wrong glossary term ×4, plus 4 spare cases of R2's choosing.
  - 10 reversal or omission errors for the AI flags.

**Data handling.**
- **Spike media folder:** `~/hl-spike-media/` on the demo laptop (decided by user, 2026-10-05). It is outside the git repository and must not be inside any cloud-synced folder. It holds recordings, cloned audio, raw transcripts and model outputs from real speakers. Create it with owner-only access (`mkdir -m 700`). Media is never committed to git.
- **Spike log:** `~/hl-spike-media/spike-log.md` (decided by user, 2026-10-05). It is **append-only**: entries are never edited or deleted, and corrections are new entries. Each entry is one line: `<ISO 8601 timestamp> | <who> | <type> | <what>`. The types are `consent`, `recording`, `transfer`, `external-upload`, `deletion`, `run` and `note`. **No raw content goes in it**: no transcripts, translations, audio or real names, only pseudonyms (Speaker A/B, R1/R2), file names, durations and hashes. It is the **external-upload log** referred to elsewhere (type `external-upload`).
- Any Kaggle datasets and kernels are deleted after the spike, and the deletion is recorded in the spike log.

## 3. Candidates (checked 2026-10-05; sources in `THIRD_PARTY_TERMS.md`)

| Stage | Slot | Candidate | Runtime | Licence / terms |
|---|---|---|---|---|
| Transcription | **A1** | faster-whisper `small` and `medium`, int8 (**provisional primary**) | Laptop CPU | MIT |
| | **A2** | Groq `whisper-large-v3` (needs `external_transcription` consent). **Dropped if Zero Data Retention does not cover the speech-to-text endpoint** (P5; consent form 3.3) | Hosted, free | No training; ZDR on |
| Translation | **T0** | IndicTrans2 En→Indic dist-200M (context-free baseline) | Laptop CPU | MIT, gated |
| | **T1/T2-G** | Gemini Flash, free tier: without context / with full context | Hosted | Free tier: training + human review; script text only |
| | **T1/T2-Q** | **One** Groq production model, chosen by a 5-segment pre-screen (run only **after** R1's reference translation is frozen) between `llama-3.3-70b-versatile` and `openai/gpt-oss-120b` (fewest critical/major errors by R1, quick read) | Hosted, free | No training |
| Meaning-check | **C-same / C-other** | Checker from the same vs. a different model family as the translator | Hosted | as above |
| Stock voice | **V0a** | MMS-TTS Tamil | Laptop CPU | CC-BY-NC-4.0 |
| | **V0b** | Indic Parler-TTS (speaker "Jaya") | Laptop CPU | Apache-2.0, gated |
| Cloned voice | **V1-cpu** | IndicF5 | Laptop CPU | Treated as non-commercial |
| | **V1-gpu** | IndicF5 (tested only if V1-cpu fails rule 6a) | Kaggle GPU batch | same |

ElevenLabs and the Groq preview models were **dropped after review**.

**Hard gates:**
- **G1 language:** documented support.
- **G2 data terms:** compatible with the data it would receive.
- **G3 access:** free, no allowlist.
- **G4 zero spend:** no payment method.
- **G5 runnable:** fits within the laptop's Docker memory limit, or within a 12-hour Kaggle session.

## 4. Measurements

All scripts and notebooks live in `spike/` and `spike/kaggle/`. They are throwaway and never imported by the app. **CPU measurements run inside the Docker Compose stack on the demo laptop** *(changed after review, because Docker's memory limits differ from bare metal)*. Each run records the model and version, prompt or version, parameters, seed, date, hardware and Docker memory limit. Timings are repeated 3 times; the median and maximum are reported, plus the first (cold) run separately.

### M1: Transcription accuracy and speed → **ADR 0017**
- **Metrics:** WER (with normalisation rules fixed in advance); **critical-token errors** (a count, out of the script's numbers, units and glossary terms); segment-boundary error (ms); real-time factor; peak RAM.
- **Method:** A1 (small, medium) and A2 on the same 16 kHz mono audio.

### M2: Translation quality, rated by R1 and R2 → **ADR 0016**
- **Input:** the reference transcript.
- **Systems:** T0, T1-G, T2-G, T1-Q, T2-Q (**5 outputs** per segment).
- **Human rating:** R1 and R2 rate independently and **blind** (shuffled, system hidden), using MQM-style categories and severities (minor 1, major 5, critical 10 points per 100 source words). Then a blind pairwise preference: T2 vs. T0 and T2 vs. T1 (for the better T2). **T1 is the same provider's T1**, e.g. T2-G vs. T1-G; the better T2 is chosen by rule 3 applied to T2-G and T2-Q [CONFIRMED 2026-10-05].
- **Calibration:** 5 practice segments, not counted.
- **Agreement between the two raters:** report **raw % agreement and the prevalence** of the label alongside Cohen's κ, because κ is unstable when a label is rare. Labels: binary "has a major or critical error", the highest severity (**linear**-weighted κ [CONFIRMED 2026-10-05]), and the pairwise choices. Agreement is reported **before** the raters discuss disagreements; the agreed labels after discussion are used for decisions.
- **Automatic (supporting only):** chrF against R1's reference. COMET only if its documentation covers Tamil [UNVERIFIED].
- **Also recorded:** requests and tokens per video minute (for M7), latency, and **digit compliance** (the % of numbers the model wrote as digits, as instructed by ADR 0008).

### M3: Rule-check and AI-flag catch rate on seeded errors → **ADR 0008**, meaning-check part of **ADR 0016**
- **Order:** (1) freeze the check rules and code version; (2) R2 writes the seeded errors; (3) run.
- **Metrics:**
  - hard-check catch rate by error type, with `UNVERIFIABLE` reported separately;
  - hard-check false-alarm rate on clean segments;
  - AI-flag catch rate on the 10 reversal and omission errors, and its false-alarm rate, for **C-same vs. C-other**.

### M4: Tamil TTS quality → **ADR 0018**, **ADR 0015**
- **Input:** the same fixed Tamil text (R1's reference, 10 utterances) for every system.
- **Systems:** V0a, V0b, V1 with the English reference, V1 with the Tamil reference.
- **Naturalness:** R1, R2 and up to 4 other named Tamil listeners (consent form 3.4; played in person on the laptop) rate 1–5, blind. The reported value is the **median pooled over 10 utterances × all raters** (report *n*).
- **Critical-content pronunciation:** R1 and R2 mark each number, unit and glossary term correct / wrong / unclear, tested **with digits and with numbers written as words**. This decides whether ADR 0008's separate speech script is needed.
- **Intelligibility (relative):** transcribe the synthesised Tamil with one fixed **local** faster-whisper model (cloned audio never goes to Groq) and compute the character error rate against the input.
- **Speaker similarity (cloned voice only):**
  - **Objective:** ECAPA-TDNN embedding cosine similarity between speaker A's real voice (the **held-out clip**, never the cloning reference; `docs/spike/TEST_SCRIPT.md` §3) and (i) speaker A's clone, and (ii) **speaker B's clone**, which is the different-speaker control *(changed after review: a stock voice was a trivial bar)*. Speaker B is matched to A in gender and rough age, with the same room and microphone. [UNVERIFIED that the embedding model runs acceptably on our CPU.]
  - **Subjective:** "same person as A?" 1–5, from listeners who know speaker A, rating **both** speaker A's clone and speaker B's clone, blind and in random order (B's clone is played to them only with B's consent 3.4 and 3.6). *(Changed 2026-10-06, round-2 fix P9.)*

### M5: Timing fit → **ADRs 0016, 0018**
- **Metric:** synthesised duration ÷ slot duration, per segment; distribution and % within ±15% (an assumed working threshold).
- **Method:** T2 output with vs. without the length constraint in the prompt, through the best stock voice at 1.0× and with a bounded tempo adjustment of ±15% (ffmpeg `atempo`).

### M6: Speed: IndicF5 on CPU (and Kaggle GPU only if needed) → **ADRs 0018, 0019, 0012**, demo plan
On the 10 fixed segments of `docs/spike/TEST_SCRIPT.md` §6 (R1's reference translation; about 3–8 s of speech each), with the same reference clip and the same seed. Cloned voices never synthesise machine output:

| Metric | Laptop CPU (in Compose) | Kaggle GPU (only if rule 6a fails) |
|---|---|---|
| Model load time (cold) | ✓ | ✓ |
| **Per-segment synthesis time** (median, max) and RTF | ✓ | ✓ |
| Peak RAM vs. the Docker memory limit (and GPU memory) | ✓ | ✓ |
| **Projected overnight render time for the whole demo project** (all cloned segments) | ✓ | n/a |
| End-to-end batch time for the demo project (upload → kernel start → load → synthesis → download → import) | n/a | ✓ |
| GPU-hours per minute of output audio → projected video minutes per week | n/a | ✓ |
| Laptop responsiveness while synthesising (is the web UI usable?) | observed | n/a |

Also on CPU: MMS-TTS and Indic Parler-TTS per-segment time and RTF; IndicTrans2 time per segment; the cost of switching models under the one-model-at-a-time rule (ADR 0005).

### M7: Free-quota capacity → **ADR 0005**
Requests, tokens and audio-seconds per video minute at each hosted stage; free-tier limits as observed (Gemini's are shown in AI Studio); projected **video minutes per day** before each quota runs out; which stage hits its limit first.

### M8: Zero-spend confirmation → **ADR 0005**
No account used has billing enabled (record the settings). Expected cost: **₹0**.

### M9: Revocation mechanics → **ADR 0006**, **ADR 0019**
- **Local:** start a 10-segment IndicF5 CPU job and revoke mid-segment. Measure the **time from the revocation commit to the subprocess being killed**; confirm nothing was saved and temp files are gone.
- **Kaggle (only if V1-gpu is tested):** while a batch runs, run `kaggle kernels delete` and `kaggle datasets delete`. Record:
  - whether the kernel stops or completes;
  - whether its output is still retrievable;
  - whether `kaggle datasets list` and `kaggle kernels list` still show them.

## 5. Decision rules (fixed before seeing results)

These rules are written now, before any results exist, so that the results can't be fitted to a preferred answer afterwards. Ties are **count-based**, because n = 1 clip *(changed after review)*.

1. **Gates first.** Any failure of G1–G5 excludes the candidate.
2. **ASR (ADR 0017):** faster-whisper stays the primary unless it makes **at least 2 more critical-token errors** than Groq on the clip. In that case, **escalate to you**, because using Groq means source audio leaves the laptop (with consent). Between faster-whisper `small` and `medium`: the smaller one, unless the larger makes at least 2 fewer critical-token errors.
3. **Translation (ADR 0016):** fewest weighted MQM points (agreed labels). A difference of **≤ 5 points per 100 words** (about one major error) is a **tie**: every system within 5 points of the best ties with it [CONFIRMED 2026-10-05]. Ties are broken by data terms (no-training preferred), then hard-check pass rate. If T2 doesn't beat T0, the result is recorded honestly; T2 is still built, and the S4 ablation decides the claim.
4. **Cloned voice in the MVP (ADR 0015):** IndicF5 qualifies only if all of these hold [CONFIRMED 2026-10-05]:
   - critical-content pronunciation errors ≤ the best stock voice's **+ 1**;
   - pooled naturalness median ≥ 3/5;
   - speaker A's clone is **more similar to A than speaker B's clone is**;
   - "same person?" median ≥ 3/5.

   The better of the English or Tamil reference is used. Otherwise the MVP uses stock voice only, and you are told first.

   **If Speaker B declines the permissions the comparison needs** (consent form 3.1, 3.5, 3.6), recruit another matched speaker. If none is available, the third condition counts as **not met** [CONFIRMED].

   **If ECAPA cannot run on the laptop** (consent form 3.5: the score is skipped, never moved elsewhere), the third condition is replaced by a listener control: among listeners who know speaker A, the "same person as A?" median is **≥ 3/5 for A's clone and ≤ 2/5 for B's clone**. If B has not given 3.4 and 3.6, this control is unavailable and the third condition counts as **not met**. The other three conditions are unchanged. *[CONFIRMED 2026-10-06, user approval of round-2 fix P9, Option A; fixed before any results exist.]*
5. **Stock voice (ADR 0018):** fewest critical-content pronunciation errors, then naturalness, then CPU speed.
6. **Runtime and demo plan:**
   - (a) **CPU is live-capable** if the median per-segment IndicF5 time is ≤ 20 s, a 3-segment scene takes ≤ 60 s, and peak RAM is ≤ 70% of the Docker memory limit.
   - (b) **Overnight CPU is sufficient** if the whole demo project's cloned segments render in ≤ 8 h.
   - **Kaggle (ADR 0019) is adopted only if (a) fails AND (b) fails** [CONFIRMED].
7. **Meaning-check:** the configuration with the highest AI-flag catch rate, provided its false-alarm rate is ≤ 30% [CONFIRMED].

## 6. Demo plan (authoritative; ADR 0012 references this section)

| Result | Plan |
|---|---|
| Rule 6a met | **Plan A:** everything live on the laptop, including a cloned-voice regeneration of one short scene |
| 6a fails, 6b met | **Plan C:** cloned-voice previews are rendered **overnight on CPU** before the demo; live regeneration uses the stock voice. **No Kaggle needed.** |
| 6a and 6b fail, Kaggle available | **Plan B:** cloned-voice previews are pre-rendered on Kaggle; live regeneration uses the stock voice |
| 6a and 6b fail, Kaggle unavailable | **Plan D:** cloned voice only for the **one short revocation scene** (rendered overnight); stock voice everywhere else |
| Rule 4 fails | **Stock-only:** consent governance is demonstrated on the speaker's recorded voice and identity record; the identity claim is narrowed |

**Live script (Plans B, C and D; Plan A is the same with a live cloned regeneration).**

| When | What |
|---|---|
| T-3 days | Pre-render the cloned-voice previews (overnight CPU or Kaggle). They are imported through the consent checks and reviewed. Build the demo seed (`build_demo_seed`; needs the speaker's Part D D1 and D2) (ADR 0020). The golden project uses stock voices only. *(The 2026-10-06 interim rule is superseded by ADR 0020.)* |
| T-1 day (the evening before) | `check_providers` (free quotas, model cache, Kaggle hours if used, and the ADR 0020 drift warnings). Run a trial `demo_reset` and rehearse from it. Record the backup screen recording (only with the speaker's Part D D3; one recording per speaker) and register it with `register_offline_copy`. |
| Live: review | Open the pre-rendered previews and **say how they were made** ("rendered overnight on this laptop", or "on a free Kaggle GPU yesterday"). |
| Live: regenerate | Request changes on a scene → regenerate with the **stock voice on CPU** so the full loop is visible. A live Kaggle dispatch is **optional and off the critical path**. |
| Live: revoke | Start a **local CPU cloned-voice job** on a multi-segment scene, so it's reliably mid-job. The Identity Owner revokes. Show: subprocess killed within seconds; job `CANCELLED (consent revoked)`; earlier cloned previews quarantined and purged; stock-voice fallback queued; deletion records; audit trail. If IndicF5 can't run on the laptop at all: the ADR 0006 §9 fallback (revoke during a Kaggle-dispatched job, show the refused import, and run the checkpoint tests on screen). A rehearsal project has no Approval yet at this point (ADR 0020 §3), so approval invalidation is shown by running its checkpoint test (CP8) on screen, not live. |
| Live: re-review, approve, export | The Reviewer accepts the single short fallback scene (scripted, about 1 minute). The Manager approves and exports. Show the evidence manifest: audit chain head, the adapter used per artefact, and the non-commercial notice. |
| If the network fails | Switch to the all-local chain (ADR 0012); translation becomes context-free, and the UI says so. |
| If something else fails | The recorded run, announced as a recording. |

## 7. Outputs

- `docs/EVALUATION.md`: each metric with its definition, TARGET (set from the spike), **MEASURED RESULT** ("spike, 1 clip, n = …") and method.
- A spike results section: excluded candidates with reasons, measured values, the outcome of each rule, and the **chosen demo plan**.
- ADRs 0015–0019 updated from "Pending spike results" to "Proposed" (or 0019 to "Deferred").
- `spike/` scripts. No media and no raw transcripts are committed.

## 8. Cost and effort

- **Money: ₹0** (confirmed in M8).
- **Quota:** small amounts of free LLM quota; Kaggle GPU only if rule 6 requires it.
- **Team time [ESTIMATE]:** about 5 working days across 2 people.
- **Rater time [ESTIMATE, revised after review]:** about **5–6 hours each** for R1 and R2 (about 150 MQM-labelled outputs + 60 pairwise choices + 40 TTS utterances), plus about 2 hours for R1's reference translation and about 1 hour for R2's seeded errors.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Kaggle phone verification fails | Only matters if rule 6 needs Kaggle; otherwise Plan C or D. |
| Gated model access is delayed | Request it on day 0; MMS-TTS (not gated) keeps the stock voice working. |
| IndicF5 doesn't fit the laptop's Docker memory | Measured in M6; Plans B or D; the ADR 0006 §9 revocation fallback. |
| Free-tier limits change during the 5 months | Provider chains (ADR 0005); quota warnings; the all-local chain needs no quota. |
| Gemini free-tier terms | Used only when `data_classification = SCRIPTED_TEAM`; text only. |
| IndicF5 licence ambiguity | Treated as non-commercial; academic scope stated. |
| n = 1 clip; κ unstable with rare labels | Count-based ties; raw agreement and prevalence reported; directional only. |
