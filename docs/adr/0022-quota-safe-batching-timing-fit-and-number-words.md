# ADR 0022: Quota-safe batching with no silent MOCK, speech timing fit, Tamil track tags, number words, intelligibility proxy

**Status:** **Accepted** (approved by the user on 2026-10-22: "approve 1,2,3,4", with extra requirements). Implemented and tested; see Consequences.

**Amends:**
- ADR 0005: chain behaviour after a real provider fails; Gemini is disabled in test mode.
- ADR 0008: Tamil number words are parsed.
- ADR 0016: prompt `loc-v3` with a length budget; batched calls.
- ADR 0021: timing, tags and proxy known issues 1–3 and 5 are addressed here.
- SPIKE_PLAN M5: the tempo cap is now 1.2×, not 1.15×.

Where they differ, this ADR takes precedence.

**Governance (user rule, same day, CLAUDE.md §11 c2):**
- The assistant never accepts, overrides, approves or exports through user accounts.
- Test runs stop at Human Review.
- The clip 01 export of the ADR 0021 run was withdrawn with `withdraw_agent_review` (audited `AGENT_REVIEW_WITHDRAWN`).

## Context

The ADR 0021 run (clip 01, 2026-10-22, `docs/trials/2026-10-22-clip01-adr0021-trial.md`) showed four problems:
1. **One meaning-check call per line** used up Gemini's free-tier limits. Then, on a 429 or 503, **the chain silently fell back to MOCK translation**.
2. **Only 2 of 14 lines fit** their time slot.
3. Export tracks were tagged `und`.
4. Number words in speech scripts were UNVERIFIABLE, so a wrong number word would only be caught by a reader.

The user chose all four fixes. Requirements:
- batch per scene or per clip;
- never silently produce MOCK text on a quota or 503 failure, and show a clear pending state;
- pass the length budget to Gemini first;
- cap the speed-up at 1.2×;
- add a blocking check for any overrun;
- keep the back-transcription CER as an automatic, labelled proxy in the evidence.

## Decision

1. **Batching.**
   - A localize job sends **one request for the whole clip** when it fits (at most 80 segments and 12,000 source characters). Otherwise it groups whole scenes into as few requests as fit.
   - The meaning check is **one request for all lines** of the job. It uses the new `MeaningCheckProvider.check_batch`; adapters without a quota keep the one-by-one default.
   - A clip now needs **2 Gemini requests** instead of 1 per scene plus 1 per line (16 for clip 01).
   - A reviewer's regeneration of one scene is 1 + 1 requests.
2. **No silent MOCK.**
   - In `run_chain`, once a real adapter has *failed* (quota, rate limit, outage, bad output), mock adapters are skipped. `NoProviderAvailable.provider_failed` is set.
   - **Localization:** the job raises `TranslationPending`. It is retried with the queue's backoff (5 s, 30 s, 120 s), then ends FAILED.
     - Scenes stay `PENDING`, with no text at all.
     - Scenes that were translated before the failure keep their translations and get previews.
     - The project page shows **"Translation pending: provider quota or outage. Nothing was machine-translated by a MOCK."**, with a **Retry** button (Manager or Media Operator only; it is not a governance action).
   - **Meaning check:** every line gets `CHECK_UNAVAILABLE`, which blocks approval until it is re-run (Retry button) or acknowledged. It is never a mock PASS.
   - A MOCK is still used, and labelled, where no real provider was *eligible*: no key, or the data-use rule for `PERSONAL` projects.
   - Gemini 5xx errors are retried once after 10 s.
3. **Length budget, prompt `loc-v3`.**
   - Each segment gets `max_speech_chars` = time available × the stock voice's measured rate at its **normal** speed. The 1.2× speed-up (§4) is kept as headroom for lines the voice speaks more slowly than average (review fix #5).
   - Gemini's `max_spoken_seconds` is the same time available, not the segment's own length.
   - "Time available" is from the line's start to the next line's start in the scene, or to the scene's end.
   - MMS-TTS Tamil: **11 characters per second**. It measured a median of 11.95 (range 9.4–14.6) on 20 synthesised lines of clip 01, and 11 is a little conservative. The calibration data is in `docs/trials/2026-10-22-clip01-adr0021-trial.md`, under "Speaking-rate calibration".
   - The prompt says speech must fit, without dropping a number, unit, negation, warning or instruction; if it can't fit, the model adds `TOO_LONG`.
   - No budget is sent when speech synthesis is off or the voice's rate is unknown.
4. **Speed-up cap of 1.2×** (`rendering.models.MAX_TEMPO`), measured against the time available, not the segment's own length.
5. **Blocking `speech_overrun` hard check.** After real (non-mock) synthesis, a line whose speech still needs more time than it has at 1.2× fails, with a 100 ms tolerance. The message gives the seconds and says "shorten the speech script". There is one result per translation version.
6. **Language tags.** Exported audio is tagged with the target language when dubbed, and the source language when subtitles-only. Subtitles are tagged with the target language (`tam` for ta-IN).
7. **Tamil number words (0–100).** A parser (`localization/tamil_numbers.py`, DRAFT [UNVERIFIED] until a Tamil rater reviews it) reads:
   - units, 10–19, the tens and 100;
   - fused compounds (இருபத்தைந்து = 25);
   - two-word compounds (இருபத்து மூன்று = 23);
   - a fixed list of case endings.

   How the numbers check uses it:
   - A **wrong number word now FAILS** (இரண்டு "2" where the source says 20).
   - Correct words PASS.
   - Plain unit words with other meanings (ஒரு "a/one", ஒன்றாக "together", ஆறு "six/river", ஏழை "poor person", எட்டு "eight/reach") count only where the source has that number. Otherwise they stay UNVERIFIABLE.
   - Larger numbers and decimals still use the stem list, so they are UNVERIFIABLE.
8. **Intelligibility proxy.**
   - After real synthesis, each line is transcribed back with faster-whisper (forced to the target language, VAD off). The character error rate against the speech script is stored on `SynthesisedSegment.intelligibility` (new field), with the label *"Intelligibility PROXY … Not a listening test; includes Whisper's own errors."*
   - It is shown on the review page, and goes into the export manifest as `intelligibility_proxy` (per-line CER, mean of the line CERs, and the label).
   - It never fails a render.
9. **Tests never spend the real quota.**
   - Gemini is unavailable in test mode unless `HL_TEST_GEMINI=1`.
   - `_post` refuses a real HTTP call in test mode unless a fake transport is injected.
   - **Found while implementing this ADR:** `.env`'s key (configured locally on 2026-10-12) was loaded in test mode, so **test runs since then sent real requests** to the free tier. This was seen directly on 2026-10-22, when tests received Google's real "daily quota used up" 429 body. Those requests failed with 429 and then silently fell back to MOCK, so the tests passed anyway. This probably used up part of the daily quota [INFERRED] and may have contributed to the 429s in the ADR 0021 run.

10. **Independent review fixes (critical-reviewer, 2026-10-22: approve with changes):**
    - **#1 (critical):** a line whose latest version has **no meaning-check result at all** now blocks approval. A retry deletes old CHECK_UNAVAILABLE rows only in the transaction that writes the new results.
    - **#2:** the CER now compares letters, combining marks (Tamil vowel signs, puḷḷi) and digits. Python's `\w` drops combining marks, which had hidden vowel errors. The ADR 0021 figure was recomputed: **0.16 over 850 characters**; it was 0.17 over 503.
    - **#3:** the proxy catches every failure as "not computed" and honours a cancel while Whisper runs.
    - **#4:** renders are queued only on success or "pending", never from a cancelled or crashed job.
    - **#5:** budget at the normal rate (§3).
    - **#6:** Retry re-sends a reviewer's failed scene regeneration, with its instruction.
    - **#7:** `manage.py test` is always test mode, even without the variable.
    - **#8:** a non-JSON reply, a dropped connection or an `OSError` is a provider failure (pending and retry), not a terminal crash.
    - **#9:** the overrun check is keyed on (voice, model, tempo cap); unresolved results from other settings are replaced.
    - **#10:** two-word compounds with ambiguous units (இருபத்து ஒன்று) are read; அஞ்சு ("five/fear") and ordinals (மூன்றாவது) count only where the source has that number.
    - **#11:** `withdraw_agent_review` deletes files only after commit, and records each reopened check and its former resolver.
    - **#12:** after a daily-quota failure, no extra meaning-check call is made.

## Consequences

- **Tests:** the full-suite result is recorded in `docs/STATUS.md` under "Tests" (entry dated 2026-10-22, ADR 0022). New files: `tests/test_adr0022.py` and `tests/test_governance.py`. The existing provider-audit and chain tests were updated to the new rules: no mock after a failure, and one audit per batch.
- Gemini requests per clip drop from about 16 to 2, measured by request count in the tests. Whether a 5-minute clip's single reply stays within the model's output limit is [UNVERIFIED]. That's why the 80-segment / 12,000-character split exists.
- Re-run of clip 01 to Human Review: see `docs/STATUS.md` and the trial note. **The review and approval are the user's.**

**Known issues:**
1. The 11 chars/s rate comes from one clip and one voice. Slower lines can still overrun; the check catches them.
2. The overrun check is created at render time. A reviewer who shortens a line triggers a re-render, which creates a new check for the new version.
3. The 80-segment / 12,000-character batch limits are implementation choices, not measured.
4. The number parser covers 0–100 only. It is a DRAFT until a rater reviews it.
5. The CER proxy needs faster-whisper. Without it, the evidence says "not computed". There is no Whisper baseline on natural Tamil speech yet, so the TTS's share of the CER can't be separated from Whisper's own errors.
6. **The numbers check compares counts, not positions.** "2 tablets 3 times" swapped to "3 tablets 2 times" still PASSes. The reviewer must catch it.
7. **The governance rule (CLAUDE.md §11 c2) is a process rule, not enforced in code.** The app can't tell an assistant from a person using the same account.
8. Each scene render loads MMS-TTS and then Whisper in one subprocess (one model at a time). That's slower; the time is reported in the clip 01 re-run.
9. Retry is not audited as an action of its own (its job is audited as `JOB_QUEUED` with the actor). It doesn't check whether the project is archived; archiving isn't enforced anywhere yet.

**Viva in 2 minutes:** "The free translator allows about twenty requests a day, so we send the whole clip in one request and check meaning in one more. If the provider fails, we never fill in fake text: the scenes wait, the page says 'translation pending', and you can retry. We tell the translator how many characters fit each line, cap the speed-up at 1.2×, and block approval if any line still runs over. We read Tamil number words, so 'two' instead of 'twenty' is caught. And we transcribe our own Tamil speech back with Whisper as a rough, clearly labelled intelligibility check."
