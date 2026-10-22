# ADR 0021: "Published public content" classification (Gemini allowed, provenance required) and MMS-TTS Tamil as the stock voice

**Status:** **Accepted** (approved by the user on 2026-10-22: "approve A1 (MMS-TTS Tamil) and B3 (Gemini for published public content), plus the scene auto-refresh fix", with conditions 1–3 below). **Implemented and tested** (see Consequences). Independent review (critical-reviewer, 2026-10-22): approve with changes, no blockers. The fixes are applied in §8, and the open items are listed under Known issues.

**Amends:**
- ADR 0005: the data-use rule for free tiers. A free-tier hosted LLM may now also receive text from `PUBLISHED_PUBLIC` projects, but only when the source URL and the licence or reuse permission are recorded.
- ADR 0014: `Project` gains `source_url`, `source_licence` and `source_attribution`, and the `PUBLISHED_PUBLIC` classification value.
- ADR 0018: the stock-voice chain is now `mms_tts_tamil → mock_stock_voice` (the mock is dev/test only). Indic Parler-TTS stays a candidate. The cloned-voice tier is **unchanged and still pending**.
- ADR 0016: the localization prompt is now `loc-v2`. `speech_text` must be fully speakable target script.

Where these ADRs differ, this ADR takes precedence.

## Context

The first real-clip runs (2026-10-22, `test_datasets/` clips 11 and 01) showed that the site could not produce its main output. The output is the same video with Tamil speech and Tamil captions:
- Translation fell back to `MockTranslationProvider` on every project marked "may contain personal data". That classification was the only honest one for real published videos, because ADR 0005 allowed Gemini only for `SCRIPTED_TEAM`.
- The only stock voice was a MOCK tone, and export refuses MOCK output.

The user asked for an end-to-end result without typing the Tamil by hand. Human review stays the governance gate. The options were compared in the session of 2026-10-22:

| | A1 MMS-TTS Tamil | A2 Indic Parler-TTS | B3 Gemini for published public content | B4 IndicTrans2 (local) |
|---|---|---|---|---|
| Quality | One fixed voice; no prosody control | Named voices, better prosody (model card) | Context-aware, with a rationale per line | Line by line, no context or rationale |
| Speed on this laptop | **Measured:** about 1.5 s per 6 s of speech, CPU | 0.9B parameters; CPU speed unmeasured | Network; free-tier rate limits | Local; unmeasured |
| Privacy | Text stays on the laptop | Same | **Text goes to Google's free tier** (may be used for training) | Text stays on the laptop |
| Access | Downloadable now | Gated (HF approval) | Key already configured | Gated (HF approval, no token yet) |
| Licence | CC-BY-NC-4.0 (non-commercial) | Apache-2.0 | Google free-tier terms | MIT |
| Viva | "A small open model reads the reviewed Tamil" | Same, heavier | "Published content only, with its licence recorded" | "Offline baseline" |

**Chosen: A1 + B3.** B4 is to follow when Hugging Face access is granted (user, 2026-10-22).

## Decision

1. **A new data classification, `PUBLISHED_PUBLIC`: "published public content whose licence permits reuse".**
   - Creating such a project **requires** `source_url` (a full http(s) address) and `source_licence` (licence or reuse permission). **Condition 1.**
   - `source_attribution` (the credit line) is **required when the licence is CC BY**.
   - A **NoDerivatives** licence is refused, because a translation is an adaptation.
   - Field lengths are validated.
   - These fields are stored on `Project` and recorded in the `PROJECT_CREATED` audit record. Every export's `evidence_manifest.json` carries them as `content_source`, together with `"verified_by_system": false`. The creator attests the licence; the system does not verify it.
   - For other classifications, the fields are stored empty.
2. **Amended data-use rule.** Gemini (and any adapter with `requires_hosted_llm_permission`) runs only for:
   - `SCRIPTED_TEAM` projects; or
   - `PUBLISHED_PUBLIC` projects whose provenance is recorded.
   It is skipped for `PERSONAL` projects, and each skip is audited as before. Only text is sent, never audio.
3. **MMS-TTS Tamil (`facebook/mms-tts-tam`) is the stock-voice adapter `mms_tts_tamil`.** **Condition 2:**
   - It is in the `speech_stock` chain only, with `supports_cloning = False`.
   - It refuses a reference clip.
   - The `speech_cloned` chain is unchanged: the identity-preserving tier stays pending (ADR 0015/0018).
4. **Unspeakable text is refused, never dropped.** The model's vocabulary is Tamil letters, space and apostrophe. The adapter therefore:
   - turns punctuation into word breaks;
   - **refuses** text that contains digits, Latin letters or other characters outside the vocabulary;
   - reports only the kind of character and how many in the error, never the text itself.
   The one documented approximation is the aytham **ஃ**, which is missing from the vocabulary and is read without it (e.g. "எஃப்" is read as "எப்"). It carries no number or negation.
5. **Prompt `loc-v2`.** `speech_text` is written entirely in the target script: numbers, units and dates as words, and names and acronyms transliterated. Subtitles keep digits (ADR 0008).
6. **The project page reloads itself when the last running job finishes.** The jobs partial polls with `?polling=1`, and the server answers with `HX-Refresh: true`. "Active" is computed over all of the project's jobs. The first load doesn't send `polling=1`, so there is no reload loop. Trade-off: anything typed on the detail page during processing (cultural notes, glossary) is lost on the reload.
7. **Evidence honesty fix (found in the run).** `quality_report.json` now records the adapter and `is_mock` for each AI flag. Before this, a MOCK meaning-check "PASS" looked like a real one. Checks saved before this change report `is_mock: null` ("not recorded"), not `false`.
8. **Review fixes (2026-10-22):**
   - **The data-use rule fails closed.** An adapter that doesn't declare `requires_hosted_llm_permission` is treated as hosted. The mocks declare `False`, and a test checks that every localization and meaning-check adapter declares the flag.
   - **New blocking hard check, `speech_speakable`.** When MMS-TTS is the stock voice that will run, a speech script the voice would refuse is caught **at review time**, before rendering. If a render is attempted anyway, the job error names the segment.

## Consequences

**Tests** (2026-10-22, `HYPERLOCALIZE_MODE=test manage.py test --noinput hyperlocalize`):
- Full-suite result: see the dated entry in `docs/STATUS.md` (Tests).
- The new tests are in `hyperlocalize/tests/test_published_public.py`. They cover:
  - the provenance rules;
  - the hosted-LLM rule;
  - the form;
  - the export `content_source` and the quality-report mock flags;
  - text preparation;
  - the stock-only adapter;
  - the jobs refresh.
- The real-model test runs with `HL_TEST_MMS=1`.

**Clip 01 end-to-end run** (2026-10-22). The clip is `test_datasets/01_handwashing_sf_health_dept_en`: 58 s, CC BY 3.0, 14 lines.

These are MEASURED RESULTS on **n = 1 clip**. They are directional, not quality claims.

| Item | Result |
|---|---|
| Path | Upload → Whisper `small` → Gemini `gemini-3.5-flash` `loc-v2` → MMS-TTS → review → approve → export `ACTIVE`. The package has the video, SRT/VTT, script, quality report and manifest. **The review, the check overrides and the approval were done by Claude in an automated test run, not by a human.** Claude acted through the demo `reviewer`/`manager` accounts, so the manifest names `manager` as the approver; the override reasons say it was automated. Never cite export 1 as human-reviewed. |
| Provenance in evidence | ✅ `content_source` with URL, CC BY 3.0, attribution, `verified_by_system: false` |
| Gemini reliability | ❌ Scene 2 fell back to MOCK twice: first on HTTP 429 (per-minute rate limit, triggered by one meaning-check call per line), then on HTTP 503. It succeeded on the third try. 3 of the approved lines carry a MOCK meaning check. |
| Translation (Claude's reading; **[UNVERIFIED]** until a Tamil-literate rater checks it) | No meaning errors found in the 14 lines. Numbers (1, 2, 3, 20, 60%) and the negation were kept. Minor issues: "rinse" became "wash" (கழுவி); one list mixes noun cases; "hand sanitizer" was transliterated; a San Francisco web address was kept for a Tamil Nadu audience, and the model didn't flag it. |
| Voice: back-transcription CER (Whisper `small`, Tamil) | 0.17 over 503 characters. This is a pessimistic proxy (Whisper `small`'s own Tamil errors are included), **not a listening test**. Number words and "இல்லை" (not) were recognised. The spelled-out web address was worst (0.40). |
| Timing fit | ❌ **2 of 14 lines fit their slot.** Tamil speech totals 79.1 s against 58.0 s of slots (1.36×). 12 lines hit the 1.15× tempo cap and still overran, by +0.1 to +2.9 s. Overlapping lines are mixed on top of each other, and the last line runs about 0.9 s past the end of the video. The structure check flagged only 1 line, because its character budget is looser than MMS-TTS's real speaking rate. |
| Speed | Analysis, localization and render of the 58 s clip took about 66 s, including Gemini calls. MMS-TTS on its own measured about 1.5 s per 6 s of audio. |

**Known issues (not fixed in this ADR):**
1. Timing: there is no measure against overrun. Options include a per-voice speaking-rate calibration, a length budget from MMS's measured rate sent in the prompt, a blocking "speech overruns its slot" check, and MMS's `speaking_rate`.
2. Free-tier rate limits: there is one meaning-check call per line, and no retry on 503.
3. Export tracks are tagged language `und`, not `tam`.
4. Whether exports should be allowed when a meaning check was MOCK is a policy question. Today they are allowed, now with the mock visible in the quality report.
5. **Number words in speech scripts are not verified automatically.** `loc-v2` writes numbers as Tamil words, and the numbers check marks them UNVERIFIABLE. A wrong number word (e.g. இரண்டு "two" where இருபது "twenty" was meant) is caught only if the reviewer reads it. The voice's refusal only guarantees that digits are never *silently dropped*. Possible fix: a small Tamil number-word parser (0–100) for the speech check.
6. The Policies page doesn't check that a provider chain matches its stage (an Administrator could put `mms_tts_tamil` in `speech_cloned`; MMS still refuses the reference clip, but late), and chain edits are not in the `POLICY_CHANGED` details.
7. The licence is self-attested (see Weaknesses).
8. The voice may refuse invisible Unicode that an LLM emits (ZWJ/ZWNJ, decomposed vowel signs). It is caught by `speech_speakable` at review time.

**Weaknesses of this decision:**
- **Licence is self-attested.** A user could mislabel personal content as published. The attestation is audited and visible in the evidence; it is not verified.
- **Gemini free tier may train on the text of published content.** That's acceptable only because the content is already public; the label says so on the form.
- **MMS-TTS is non-commercial and one voice.** HyperLocalize stays an academic demonstrator (THIRD_PARTY_TERMS).

**Viva in 2 minutes:** "Published videos can use the hosted translator, but only if the project records where the video came from and its licence, and that record travels into the export evidence. The licence is attested by the user, not verified, and the evidence says so. The Tamil voice is a small open model that runs on the laptop. It is a stock voice and never imitates a person. If the script has a digit or an English word it can't pronounce, the review screen blocks it and the voice refuses it, so nothing is silently dropped. Numbers written as Tamil words still need the reviewer to confirm them; we don't parse them yet."

**Trial record:** `docs/trials/2026-10-22-clip01-adr0021-trial.md` (raw timing table and the back-transcription output). The script is `scripts/backtranscribe_cer.py`.
