"""M5: timing fit of synthesised Tamil speech (SPIKE_PLAN §4 M5).

ratio = synthesised duration / slot duration, per segment.
- At 1.0x speed: a segment fits if |ratio - 1| <= tolerance.
- With a bounded tempo change (ffmpeg atempo, at most +/- max_tempo_change):
  the tempo factor is the ratio clamped to [1 - max, 1 + max]; the residual
  ratio after that change must be within tolerance.
The 15% tolerance and 15% tempo bound are working assumptions from the plan.

Usage:
    python3 -m hlspike.timing_fit --slots slots.csv --audio-dir DIR [--out fit.json]
slots.csv has the header seg_id,start_s,end_s; DIR holds <seg_id>.wav (PCM WAV).
"""

import argparse
import csv
import json
import statistics
import wave
from pathlib import Path

TOLERANCE = 0.15
MAX_TEMPO_CHANGE = 0.15


def wav_duration_s(path: Path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def residual_after_tempo(ratio: float, max_change: float = MAX_TEMPO_CHANGE) -> float:
    tempo = min(max(ratio, 1 - max_change), 1 + max_change)
    return ratio / tempo


def summarise(ratios: dict[str, float], tolerance: float = TOLERANCE, max_change: float = MAX_TEMPO_CHANGE) -> dict:
    if not ratios:
        raise ValueError("no segments")
    values = list(ratios.values())
    residuals = {seg: residual_after_tempo(r, max_change) for seg, r in ratios.items()}
    within = [seg for seg, r in ratios.items() if abs(r - 1) <= tolerance + 1e-9]
    within_tempo = [seg for seg, r in residuals.items() if abs(r - 1) <= tolerance + 1e-9]
    return {
        "n": len(values),
        "ratio_min": min(values),
        "ratio_median": statistics.median(values),
        "ratio_max": max(values),
        "pct_within_tolerance_at_1x": 100 * len(within) / len(values),
        "pct_within_tolerance_with_tempo": 100 * len(within_tempo) / len(values),
        "not_fitting_with_tempo": sorted(set(ratios) - set(within_tempo)),
        "tolerance": tolerance,
        "max_tempo_change": max_change,
    }


def read_slots(path: Path) -> dict[str, float]:
    with path.open(newline="", encoding="utf-8") as f:
        return {row["seg_id"]: float(row["end_s"]) - float(row["start_s"]) for row in csv.DictReader(f)}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slots", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    slots = read_slots(args.slots)
    ratios = {}
    for seg_id, slot_s in slots.items():
        wav = args.audio_dir / f"{seg_id}.wav"
        if not wav.exists():
            parser.error(f"missing audio for {seg_id}: {wav}")
        ratios[seg_id] = wav_duration_s(wav) / slot_s
    result = {"per_segment_ratio": ratios, "summary": summarise(ratios)}
    output = json.dumps(result, indent=2)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
