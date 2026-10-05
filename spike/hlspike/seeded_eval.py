"""M3: hard-check catch rate on R2's seeded errors (SPIKE_PLAN §4 M3, ADR 0008).

Input: one JSON object per line:
    {"id": "E01", "source": "<English>", "target": "<Tamil with an error>",
     "error_type": "number_wrong_western", "expected": "FAIL"}
expected is one of:
    FAIL          the rule checks should fail it
    UNVERIFIABLE  e.g. a number written as a Tamil word
    CLEAN         a correct segment (used for the false-alarm rate)
    AI_FLAG       a reversal/omission error meant for the AI flagger; the
                  rule checks are not expected to catch it (reported separately)

"Caught" means the overall result is not PASS. UNVERIFIABLE results are
reported separately from FAIL, as the spike plan requires.

Usage:
    python3 -m hlspike.seeded_eval --seeded seeded.jsonl [--out report.json]
Refuses to run if the rules changed since hlspike.freeze --write.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from .checks import CheckSet, check_segment, read_jsonl
from .freeze import changed_since_freeze
from .numbers import PASS, UNVERIFIABLE

EXPECTED_VALUES = {"FAIL", "UNVERIFIABLE", "CLEAN", "AI_FLAG"}


def evaluate(items: list[dict], checkset: CheckSet) -> dict:
    by_type = defaultdict(lambda: {"n": 0, "caught": 0, "caught_as_fail": 0, "caught_as_unverifiable": 0, "missed_ids": []})
    clean = {"n": 0, "false_alarms": 0, "false_alarm_ids": []}
    ai_flag = {"n": 0, "incidentally_caught": 0}

    for item in items:
        if item["expected"] not in EXPECTED_VALUES:
            raise ValueError(f"{item['id']}: unknown expected value {item['expected']!r}")
        overall = check_segment(item["id"], item["source"], item["target"], checkset).overall
        caught = overall != PASS

        if item["expected"] == "CLEAN":
            clean["n"] += 1
            if caught:
                clean["false_alarms"] += 1
                clean["false_alarm_ids"].append(item["id"])
        elif item["expected"] == "AI_FLAG":
            ai_flag["n"] += 1
            ai_flag["incidentally_caught"] += caught
        else:
            row = by_type[item["error_type"]]
            row["n"] += 1
            if caught:
                row["caught"] += 1
                row["caught_as_unverifiable" if overall == UNVERIFIABLE else "caught_as_fail"] += 1
            else:
                row["missed_ids"].append(item["id"])

    seeded_n = sum(r["n"] for r in by_type.values())
    seeded_caught = sum(r["caught"] for r in by_type.values())
    return {
        "by_error_type": dict(by_type),
        "hard_check_catch_rate": _rate(seeded_caught, seeded_n),
        "hard_check_catch_rate_excluding_unverifiable": _rate(sum(r["caught_as_fail"] for r in by_type.values()), seeded_n),
        "clean": clean,
        "false_alarm_rate": _rate(clean["false_alarms"], clean["n"]),
        "ai_flag_items": ai_flag,
    }


def _rate(numerator: int, denominator: int) -> dict:
    return {"value": numerator / denominator if denominator else None, "numerator": numerator, "denominator": denominator}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeded", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    changed = changed_since_freeze()
    if changed is None:
        sys.exit("Refusing to run: rules were never frozen (python3 -m hlspike.freeze --write).")
    if changed:
        sys.exit("Refusing to run: rules changed since the freeze: " + ", ".join(changed))

    report = evaluate(read_jsonl(args.seeded), CheckSet.load())
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
