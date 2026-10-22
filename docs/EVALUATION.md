# Evaluation: metrics (TARGET vs MEASURED RESULT)

The methods and thresholds are fixed in `docs/SPIKE_PLAN.md`, before any results exist. Nothing below has been measured on real data unless the MEASURED column says so.

| Metric | Definition | TARGET | MEASURED RESULT | Method |
|---|---|---|---|---|
| Transcription accuracy (M1) | WER / critical-token errors on the test clip | Rule 2 (SPIKE_PLAN §5) | **NOT MEASURED** (no consented recording yet) | `spike/hlspike/asr_score.py` |
| Translation quality (M2) | MQM points per 100 words; pairwise preference; chrF as support | Rule 3 | **NOT MEASURED** (needs a Tamil-literate rater) | `spike/hlspike/translation_eval.py` |
| Rule-check catch rate (M3) | Share of seeded errors caught | ADR 0008 | **NOT MEASURED** (seeded set not written) | `spike/hlspike/seeded_eval.py` |
| Speech quality and similarity (M4) | Naturalness median; pronunciation of critical content; speaker similarity | Rule 4 | **NOT MEASURED** (no listening test). Proxy only, pre-spike, clip 01 (not the spike clip), MMS-TTS stock voice: Whisper-small Tamil back-transcription CER **0.17** over 503 characters (2026-10-22, ADR 0021). Pessimistic: includes Whisper's own errors | SPIKE_PLAN M4; `scripts/backtranscribe_cer.py`; raw output in `docs/trials/2026-10-22-clip01-adr0021-trial.md` |
| Timing fit (M5) | Share of segments within ±15 % of their slot | Assumed working threshold | Spike clip **NOT MEASURED**. Pre-spike, clip 01, MMS-TTS + Gemini `loc-v2`: **2/14** within ±15 %; total speech 79.1 s vs 58.0 s of slots (2026-10-22, ADR 0021) | `spike/hlspike/timing_fit.py`; ADR 0021 run used stored synthesis durations |
| Speed (M6) | Model load, per-segment time, peak RAM | Rule 6 | **NOT MEASURED** (no real model run) | `spike/hlspike/bench.py` |
| Consent enforcement | Identity use refused in every denied state; revocation stops a running job | All denied states refused; stop within seconds | **MEASURED (automated tests, 2026-10-06):** every tested denied state is refused. The mid-job stop passed its test bound (under 8 s). The actual stop time was **not recorded** | `identity/tests.py`, `tests/test_identity_workflow.py`, `tests/test_review_fixes.py` |
| Review gate integrity | No approval with open checks, unaccepted scenes, stale previews or invalid consent; no export of MOCK output | 0 bypasses | **MEASURED (automated tests):** 0 bypasses in the tested cases | `tests/test_workflow.py` |
| Audit integrity | Edits are rejected; tampering is detected by the verifier | Detected | **MEASURED (automated tests):** rejected and detected in the tested cases | `audit/tests.py` |
| Context ablation | Context on vs off vs a plain MT baseline | Show whether context helps | **NOT MEASURED** | Phase 0 §8, SPIKE_PLAN M2 |
