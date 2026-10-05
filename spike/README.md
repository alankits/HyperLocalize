# Spike tooling (throwaway)

Scripts for `docs/SPIKE_PLAN.md`. **Never imported by the application.** These scripts use only the Python standard library (3.10+; tested on 3.14), so nothing needs installing.

**Status:** these tools are unit-tested on **synthetic inputs only**. None has been run on real spike data, because no recordings, model outputs or rater data exist yet. Nothing here produces a MEASURED RESULT until it is run on real data.

## Run the tests

```bash
cd spike
python3 -m unittest discover -s tests -t .
```

## Tools

| Module | Spike step | What it does |
|---|---|---|
| `hlspike.script_export` | §2 | Exports the 27 segments of `docs/spike/TEST_SCRIPT.md` as JSONL or plain text |
| `hlspike.asr_score` | M1 | WER, critical-token errors (numbers, units, glossary, "once a day"), and segment-boundary error. Normalisation rules are in `data/m1_normalisation.json`. |
| `hlspike.checks` | M3, ADR 0008 | Hard checks per segment: numbers (with the `UNVERIFIABLE` fail-safe), units, glossary terms, structure |
| `hlspike.freeze` | M3 | Records hashes of the rule files. **Run `--write` before R2 writes the seeded errors.** |
| `hlspike.seeded_eval` | M3 | Catch rate by error type (`UNVERIFIABLE` reported separately) and false-alarm rate. **Refuses to run if the rules changed after the freeze.** |
| `hlspike.translation_eval` | M2, §5 rule 3 | Blind MQM rating sheet and key; MQM points per 100 source words; rater agreement (raw %, prevalence, kappa); chrF against R1's reference; digit compliance; hard-check pass rate; rule 3 decision; blind pairwise sheet and tally |
| `hlspike.chrf` | M2 | chrF with sacreBLEU's defaults (stdlib). Matches sacreBLEU 2.6.0 on NFC input (cross-checked 2026-10-05) |
| `hlspike.agreement` | M2 | Cohen's kappa, linear-weighted kappa, raw agreement and prevalence |
| `hlspike.timing_fit` | M5 | Synthesised duration ÷ slot duration; % within ±15% at 1.0× and with bounded tempo |
| `hlspike.bench` | M1/M6 | Times any command N times: cold run, median, max, peak RSS, real-time factor, hardware, Docker (cgroup) memory limit |
| `hlspike.rules` | §5 rules 3 and 6, §6 | The live and overnight thresholds and the demo-plan choice, fixed in code before results exist |

Each module's docstring has its usage line (`python3 -m hlspike.<module> --help`).

## Data files: who fills them in, and when

| File | State | Must be done before |
|---|---|---|
| `data/units.json` | English forms only. **`ta_forms` empty: R1/R2 fill them in.** | Freeze |
| `data/glossary.json` | English forms only. **`ta_forms` and `ta_stem` empty: R1/R2 fill them in.** | Freeze |
| `data/ta_number_word_stems.txt` | **Draft by the assistant, [UNVERIFIED]. R1/R2 must review it.** | Freeze |
| `data/m1_normalisation.json` | Follows `TEST_SCRIPT.md` §2b | Any ASR output is seen |
| `data/m2_data_terms.json` | Copied from `SPIKE_PLAN.md` §3 (which providers may train on our data) | The M2 tally; re-check if the terms change |

Until the Tamil forms are filled in, units written in Tamil give FAIL and glossary terms give UNVERIFIABLE. This is deliberate: an empty lexicon never produces PASS.

## Working files

**Real spike data** (recordings, cloned audio, raw transcripts and model outputs from real speakers) goes in `~/hl-spike-media/`, outside the repository, and never in `spike/work/`. The spike log is `~/hl-spike-media/spike-log.md` (`SPIKE_PLAN.md` §2, data handling).

`spike/work/` is git-ignored scratch space for **synthetic** test inputs and tool output only. **Never commit media or raw transcripts** (`SPIKE_PLAN.md` §7).

## Known limitations (by design or not yet solved)

- **Number words:** Tamil number words are detected by stem prefix and never parsed (ADR 0008 MVP). Common words such as ஒரு ("a") also match, so expect some false `UNVERIFIABLE` results. M3 measures how often.
- **Units:** the check tests whether each unit is present, not how many times it appears. If a source mentions "ml" twice, one "ml" in the target passes.
- **Tamil prefix matching** can match unrelated words that start with a lexicon form. This errs towards false alarms, and the false-alarm rate measures it.
- **"Mostly Latin script"** counts letters with `str.isalpha()`. Tamil vowel signs are not counted, which slightly raises the Latin share.
- **Boundary error** is the distance from each reference boundary to the nearest ASR boundary. It is a proxy, because ASR segments don't line up one-to-one with ours.
- **`bench` peak RSS** comes from `os.wait4` for the direct child. Whether memory used by grandchildren is included is [UNVERIFIED], so run the model in-process in the timed command. Run `bench` **inside** the Compose container so the cgroup memory limit is recorded.
- **M2 choices made by the assistant before any data (2026-10-05):**
  - "Highest severity" agreement uses **linear** weighted kappa; the plan only says "weighted".
  - A rule 3 tie means **within 5 points of the best** system.
  - "T2 vs T1 (for the better T2)" is read as the **same provider's** T1 (T2-G vs T1-G) [INFERRED].
  - The better T2 is chosen by rule 3 itself, applied to T2-G and T2-Q.
- **M2 blindness:** the sheet hides system names and shuffles the order, but a rater may still recognise a system by its style (for example, an LLM's punctuation). The tool cannot prevent this.
- **M2 digit compliance** counts numbers the way the hard checks do, so "one sachet" counts as the number 1. A natural "ஒரு பொட்டலம்" therefore lowers digit compliance.
- **M2 rating files** go in `~/hl-spike-media/`, like the other model outputs. Calibration (TEST_SCRIPT §1b) is a separate `prepare-mqm` run into its own folder, so it is never counted.
- **Not built yet:** the ECAPA similarity script (M4), the faster-whisper, IndicF5, Gemini and Groq runners, and the AI meaning-check (M3). These need the models, keys and signed consent first.
