"""M1: transcription accuracy (docs/SPIKE_PLAN.md §4 M1, ADR 0017).

Computes, for one reference transcript and one ASR hypothesis:
- WER after normalisation (rules in data/m1_normalisation.json, fixed in advance);
- critical-token errors: numbers, units, glossary terms and "once a day"
  (docs/spike/TEST_SCRIPT.md §2b), counted on a word alignment;
- segment-boundary error (optional): for each hand-marked reference boundary,
  the distance in ms to the nearest boundary in the ASR output.

Usage:
    python3 -m hlspike.asr_score --ref ref.txt --hyp hyp.json \
        [--ref-boundaries boundaries.csv] [--out result.json]

hyp may be plain text, or JSON shaped {"segments": [{"start": s, "end": s, "text": "..."}]}.
boundaries.csv has the header seg_id,start_s,end_s.
"""

import argparse
import csv
import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path

from . import DATA_DIR
from .english_numbers import parse_number_words

NORMALISATION_FILE = DATA_DIR / "m1_normalisation.json"

TOKEN_RE = re.compile(r"\d+(?:[.,:]\d+)*|[a-z]+(?:'[a-z]+)?")
NUMBER_TOKEN_RE = re.compile(r"^\d+(?:[.:]\d+)?$")


def load_rules(path: Path = NORMALISATION_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- normalisation

def normalise_words(text: str, rules: dict) -> list[str]:
    """Lower-case, drop punctuation, apply spelling equivalents, and turn number
    words into digits. This is the token list used for WER."""
    text = text.lower()
    for dotted, plain in rules["dotted_abbreviations"].items():
        text = text.replace(dotted, plain)
    words = []
    for token in TOKEN_RE.findall(text):
        if re.fullmatch(r"\d{1,3}(?:,\d{3})+", token):  # 1,000 -> 1000
            token = token.replace(",", "")
        words.append(rules["equivalents"].get(token, token))
    return _number_words_to_digits(words)


def _number_words_to_digits(words: list[str]) -> list[str]:
    out = []
    i = 0
    while i < len(words):
        parsed = parse_number_words(words, i)
        if parsed is None:
            out.append(words[i])
            i += 1
        else:
            value, i = parsed
            out.append(str(value))
    return out


def join_phrases(words: list[str], rules: dict) -> list[str]:
    """Replace multi-word critical phrases ("loose stool") with one token
    ("loose_stool") so that each critical item is one alignment position."""
    phrases = sorted(
        ((p.split(), canonical) for p, canonical in rules["phrases"].items()),
        key=lambda item: -len(item[0]),  # longest phrase first
    )
    out = []
    i = 0
    while i < len(words):
        for phrase_words, canonical in phrases:
            if words[i:i + len(phrase_words)] == phrase_words:
                out.append(canonical)
                i += len(phrase_words)
                break
        else:
            out.append(words[i])
            i += 1
    return out


def is_critical(token: str, rules: dict) -> bool:
    return bool(NUMBER_TOKEN_RE.match(token)) or token in rules["critical"]


# -------------------------------------------------------------------- alignment

@dataclass
class Alignment:
    """Edit operations from a Levenshtein alignment.
    Each op is (kind, ref_index or None, hyp_index or None), kind in
    'equal', 'sub', 'del' (word missing from hyp), 'ins' (extra word in hyp)."""
    ops: list[tuple[str, int | None, int | None]] = field(default_factory=list)

    def count(self, kind: str) -> int:
        return sum(1 for op in self.ops if op[0] == kind)


def align(ref: list[str], hyp: list[str]) -> Alignment:
    rows, cols = len(ref) + 1, len(hyp) + 1
    cost = [[0] * cols for _ in range(rows)]
    for i in range(rows):
        cost[i][0] = i
    for j in range(cols):
        cost[0][j] = j
    for i in range(1, rows):
        for j in range(1, cols):
            same = ref[i - 1] == hyp[j - 1]
            cost[i][j] = min(
                cost[i - 1][j - 1] + (0 if same else 1),
                cost[i - 1][j] + 1,
                cost[i][j - 1] + 1,
            )
    # Walk back from the bottom-right corner.
    ops = []
    i, j = len(ref), len(hyp)
    while i > 0 or j > 0:
        if i > 0 and j > 0 and cost[i][j] == cost[i - 1][j - 1] + (0 if ref[i - 1] == hyp[j - 1] else 1):
            ops.append(("equal" if ref[i - 1] == hyp[j - 1] else "sub", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i > 0 and cost[i][j] == cost[i - 1][j] + 1:
            ops.append(("del", i - 1, None))
            i -= 1
        else:
            ops.append(("ins", None, j - 1))
            j -= 1
    ops.reverse()
    return Alignment(ops)


def wer(ref: list[str], hyp: list[str]) -> float:
    if not ref:
        raise ValueError("reference is empty")
    a = align(ref, hyp)
    return (a.count("sub") + a.count("del") + a.count("ins")) / len(ref)


# -------------------------------------------------------------- critical tokens

def critical_token_errors(ref_text: str, hyp_text: str, rules: dict) -> dict:
    ref = join_phrases(normalise_words(ref_text, rules), rules)
    hyp = join_phrases(normalise_words(hyp_text, rules), rules)
    errors = []
    inserted = []
    total = 0
    for kind, i, j in align(ref, hyp).ops:
        if i is not None and is_critical(ref[i], rules):
            total += 1
            if kind != "equal":
                errors.append({"ref": ref[i], "hyp": hyp[j] if j is not None else None, "kind": kind})
        elif kind == "ins" and is_critical(hyp[j], rules):
            inserted.append(hyp[j])
    return {"critical_total": total, "critical_errors": len(errors), "errors": errors, "inserted_critical": inserted}


# ------------------------------------------------------------ boundary error

def boundary_errors_ms(ref_boundaries_s: list[float], hyp_boundaries_s: list[float]) -> dict:
    """Distance from each reference boundary to the nearest hypothesis boundary.
    A simple proxy: ASR segments need not line up one-to-one with ours."""
    if not ref_boundaries_s or not hyp_boundaries_s:
        raise ValueError("need at least one boundary on each side")
    distances = [min(abs(r - h) for h in hyp_boundaries_s) * 1000 for r in ref_boundaries_s]
    return {"n": len(distances), "median_ms": statistics.median(distances), "max_ms": max(distances)}


def read_ref_boundaries(path: Path) -> list[float]:
    points = set()
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            points.add(float(row["start_s"]))
            points.add(float(row["end_s"]))
    return sorted(points)


def read_hypothesis(path: Path) -> tuple[str, list[float] | None]:
    """Return (text, boundaries or None) from a .json or plain-text hypothesis."""
    raw = path.read_text(encoding="utf-8")
    if path.suffix != ".json":
        return raw, None
    segments = json.loads(raw)["segments"]
    text = " ".join(s["text"] for s in segments)
    points = sorted({float(s["start"]) for s in segments} | {float(s["end"]) for s in segments})
    return text, points


def score(ref_text: str, hyp_text: str, rules: dict) -> dict:
    ref_words = normalise_words(ref_text, rules)
    hyp_words = normalise_words(hyp_text, rules)
    result = {"wer": wer(ref_words, hyp_words), "ref_words": len(ref_words)}
    result.update(critical_token_errors(ref_text, hyp_text, rules))
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", type=Path, required=True)
    parser.add_argument("--hyp", type=Path, required=True)
    parser.add_argument("--ref-boundaries", type=Path)
    parser.add_argument("--rules", type=Path, default=NORMALISATION_FILE)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    rules = load_rules(args.rules)
    hyp_text, hyp_points = read_hypothesis(args.hyp)
    result = score(args.ref.read_text(encoding="utf-8"), hyp_text, rules)
    if args.ref_boundaries:
        if hyp_points is None:
            parser.error("--ref-boundaries needs a JSON hypothesis with segment times")
        result["boundaries"] = boundary_errors_ms(read_ref_boundaries(args.ref_boundaries), hyp_points)

    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
