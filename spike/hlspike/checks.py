"""ADR 0008 hard checks for one translated segment, plus a CLI for a whole file.

Checks: numbers, units, glossary terms, structure (empty, untranslated,
mostly Latin script, too long). Negation and meaning reversal are NOT
rule-checked (ADR 0008: Tamil negation lives in the verb); those go to the
AI flagger and the human reviewer.

Overall result: FAIL if any check fails, else UNVERIFIABLE if any check is
unverifiable, else PASS. Anything other than PASS would block approval.

Usage:
    python3 -m hlspike.checks --segments segs.jsonl [--out results.jsonl]
segs.jsonl: one {"id": ..., "source": "<English>", "target": "<Tamil>"} per line,
optionally with "max_chars" for the length budget.
"""

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import DATA_DIR
from .lexicon_checks import check_glossary, check_units, load_json
from .numbers import FAIL, PASS, STEMS_FILE, UNVERIFIABLE, check_numbers, load_tamil_number_stems

UNITS_FILE = DATA_DIR / "units.json"
GLOSSARY_FILE = DATA_DIR / "glossary.json"
LATIN_SHARE_LIMIT = 0.5  # "mostly Latin script" means more than half the letters


@dataclass
class CheckSet:
    """The frozen inputs the checks need: lexicons and number-word stems."""
    units: list[dict]
    glossary: list[dict]
    stems: list[str]

    @classmethod
    def load(cls, units=UNITS_FILE, glossary=GLOSSARY_FILE, stems=STEMS_FILE) -> "CheckSet":
        return cls(load_json(units), load_json(glossary), load_tamil_number_stems(stems))


@dataclass
class SegmentReport:
    id: str
    overall: str
    checks: dict = field(default_factory=dict)  # name -> {"status": ..., "details": [...]}


def check_structure(source: str, target: str, max_chars: int | None = None) -> tuple[str, list[str]]:
    if not target.strip():
        return FAIL, ["target is empty"]
    details = []
    if " ".join(target.lower().split()) == " ".join(source.lower().split()):
        details.append("target is the same as the source (untranslated)")
    letters = [ch for ch in target if ch.isalpha()]
    latin = sum(1 for ch in letters if ch.isascii())
    if letters and latin / len(letters) > LATIN_SHARE_LIMIT:
        details.append(f"target is mostly Latin script ({latin}/{len(letters)} letters)")
    if max_chars is not None and len(target) > max_chars:
        details.append(f"target is {len(target)} characters; budget is {max_chars}")
    return (FAIL, details) if details else (PASS, [])


def check_segment(seg_id: str, source: str, target: str, checkset: CheckSet, max_chars: int | None = None) -> SegmentReport:
    results = {
        "structure": check_structure(source, target, max_chars),
        "numbers": check_numbers(source, target, checkset.stems),
        "units": check_units(source, target, checkset.units),
        "glossary": check_glossary(source, target, checkset.glossary),
    }
    statuses = {status for status, _ in results.values()}
    overall = FAIL if FAIL in statuses else UNVERIFIABLE if UNVERIFIABLE in statuses else PASS
    return SegmentReport(seg_id, overall, {name: {"status": s, "details": d} for name, (s, d) in results.items()})


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--segments", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    checkset = CheckSet.load()
    reports = [check_segment(s["id"], s["source"], s["target"], checkset, s.get("max_chars")) for s in read_jsonl(args.segments)]
    lines = [json.dumps(asdict(r), ensure_ascii=False) for r in reports]
    if args.out:
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        print("\n".join(lines))
    print(json.dumps(dict(Counter(r.overall for r in reports))))


if __name__ == "__main__":
    main()
