# Live trial: Gemini candidate adapters (2026-10-12)

**What this is:** the first live call of the candidate Gemini adapters (ADR 0005 and ADR 0016, still pending the spike). It is a smoke test, **not** a quality evaluation and **not** a spike run. Nothing here chooses a provider.

## Setup [CONFIRMED]
- **Databases:** a throwaway database (`hl_gemini_trial`) and media folder in the session scratchpad. The dev database was not touched.
- **Mode and data:** `HYPERLOCALIZE_MODE=dev`. `seed_demo` created the demo project: SCRIPTED_TEAM, 11 English segments of team-written ORS text from TEST_SCRIPT scenes 1–2, with health facts [UNVERIFIED].
- **What was sent:** text only. No audio, video or personal data. Google AI Studio free-tier key. The adapter code was unchanged.
- **Model:** set for each run with the `HL_GEMINI_MODEL` environment variable. The repository default was not changed.

## Runs [MEASURED]
| Run | Model | Result |
|---|---|---|
| 1 | `gemini-2.5-flash` (repo default) | HTTP 404 "no longer available to new users". The chain fell back to the MOCK for all 11 segments. The model-list endpoint still lists it, so a model-list check alone is not proof that a model can be called. |
| 2 | `gemini-3.8-flash` (named in Google's 404 message) | Requests hung beyond 60 s (the adapter timeout) and also beyond 300 s. A one-word probe got HTTP 503 "high demand". MOCK fallback; the localize job took 291 s. |
| 3 | `gemini-3.5-flash` | Localization: **11/11 segments from Gemini**, `is_mock=False`, `is_fallback=False`. Meaning check: 8/11 from Gemini, **3 fell back to the MOCK**. The full pipeline (4 jobs) took 47.6 s wall-clock; the localize job took 45.6 s for 2 scenes, 2 localization calls and 11 meaning-check calls. One direct scene call: 8.6 s, 1060 prompt tokens, 577 output tokens, 935 "thinking" tokens. |

The usage ledger recorded `gemini_localization` 2 requests and `gemini_meaning_check` 8 requests. The quota warnings therefore have real data to work with.

Replay of 11 meaning checks back to back: segment 9 got HTTP 429 at about 35 s, and the next call about 5 s later succeeded. **[INFERRED]** The cause is a per-minute request limit, not the daily quota.

## Output observations
These are the assistant's reading, **[INFERRED]**. They are not a rating; R1 or R2 must judge the Tamil.
- All output is in Tamil script. Subtitles keep digits (`1`, `24`). The speech text spells them out (`ஒரு`) and writes ORS as `ஓ.ஆர்.எஸ்`, as the prompt asks.
- **Possible meaning shift not flagged:** S02 "it **can be** dangerous" became `இது ஆபத்தானது` ("it is dangerous"). The hedge is dropped, and the Gemini meaning check did not flag it. This is an example of why AI flags are advisory and human review is the gate.
- The meaning check flagged an ADDITION in S07: `நன்றாக` ("well, thoroughly") was added.
- The rationales are generic ("Translated clearly for caregiver audience"). They help a reviewer little.
- **Hard checks did their job:**
  - three segments were over the length budget;
  - the unit checks for litre and hour FAILED, because the Tamil unit lexicon is still empty;
  - the glossary checks were UNVERIFIABLE (empty lexicon, by design).

## Defects found
1. **Model default is stale:** the default `HL_GEMINI_MODEL=gemini-2.5-flash` in `settings.py` and `.env.example` can't be called by new keys.
2. **429 misclassified** (`pipeline/providers/gemini.py`, `_post`): any 429 whose text contains "quota" becomes `QuotaExhausted`. Google's per-minute 429s contain that word too. So a short pause is treated as the daily quota running out, and the chain falls through to the next adapter instead of retrying.
3. **Localization skip reasons not audited** (`localization/services.py`, `localize_scene`): the audit filter matches the substring "Error". The fall-through exception names (`Unavailable`, `RateLimited`, `QuotaExhausted`, `ProviderOutputInvalid`) contain neither "Error" nor "data-use rule", so the 404 left only a bare `PROVIDER_FALLBACK`.
4. **Meaning-check fallback is silent** (`_run_meaning_check`): there is no audit record when the chain falls back. The MOCK keyword flag is stored next to real AI flags; it is tagged `is_mock` in its detail.
5. **Quota windows:** `pipeline/quota.py` supports only 24 h and 7 day windows. The limit hit here was per-minute.
