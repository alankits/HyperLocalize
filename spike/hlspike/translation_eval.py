"""M2: translation quality (SPIKE_PLAN §4 M2, §5 rule 3, ADR 0016).

Steps, in this order:

1. prepare-mqm: build ONE blind rating sheet for all 5 systems. Items are
   shuffled and get neutral ids (M001...); the system names go only into the
   key file. Do NOT give the key to R1 or R2. Run it once for the 5
   calibration sentences (TEST_SCRIPT §1b) into a separate folder for
   practice, then once for the 27 rated segments.
2. R1 and R2 each fill in their own copy of the annotation template, without
   talking to each other. Then they discuss disagreements and write one
   agreed file. Keep all three files: agreement is measured on the first two,
   and the decision uses the agreed file.
3. tally: MQM points per 100 source words, rater agreement, chrF against R1's
   reference, digit compliance, hard-check pass rate, and the rule 3 decision
   (when the agreed file exists). It also names the better T2 for step 4.
4. prepare-pairs: blind pairwise sheet, e.g. --compare T2-G:T0 --compare
   T2-G:T1-G. The left/right order is random per pair. Then run tally again
   with the pairwise files.

File formats (all UTF-8):
- source.jsonl:   {"id": "S01", "text": "<English>"} (hlspike.script_export, or
                  the verbatim reference transcript split into segments)
- <system>.jsonl: {"id": "S01", "target": "<Tamil>"}; R1's reference has the same shape
- annotations CSV: item_id,category,severity,note. One row per error. An item
  with no errors gets ONE row with severity "none" and an empty category.
  Every item must appear, so a skipped item is an error, not a clean score.
- pair choices CSV: pair_id,choice,note, where choice is 1, 2 or same.

Usage:
    python3 -m hlspike.translation_eval prepare-mqm --source src.jsonl \
        --system T0=t0.jsonl --system T1-G=t1g.jsonl ... --out-dir DIR [--seed N]
    python3 -m hlspike.translation_eval prepare-pairs --source src.jsonl \
        --system T0=... --system T1-G=... --system T2-G=... \
        --compare T2-G:T0 --compare T2-G:T1-G --out-dir DIR [--seed N]
    python3 -m hlspike.translation_eval tally --source src.jsonl \
        --reference ref.jsonl --system T0=... (all 5) --mqm-key DIR/mqm_key.json \
        --r1 r1.csv --r2 r2.csv [--agreed agreed.csv] \
        [--pairs-key DIR/pairs_key.json --pairs-r1 p1.csv --pairs-r2 p2.csv \
         [--pairs-agreed pa.csv]] [--out report.json]

Not done here (recorded by the translation runners when they exist): requests,
tokens and latency per video minute.
"""

import argparse
import csv
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from . import DATA_DIR
from .agreement import binary_summary, cohen_kappa, linear_weighted_kappa, raw_agreement
from .checks import CheckSet, check_segment, read_jsonl
from .chrf import corpus_chrf, sentence_chrf
from .freeze import changed_since_freeze
from .numbers import PASS, source_numbers, target_numbers
from .rules import TRANSLATION_TIE_POINTS, rule3

DATA_TERMS_FILE = DATA_DIR / "m2_data_terms.json"

SEVERITY_POINTS = {"none": 0, "minor": 1, "major": 5, "critical": 10}  # SPIKE_PLAN M2
SEVERITY_RANK = {"none": 0, "minor": 1, "major": 2, "critical": 3}
# MQM-style top-level categories from PHASE0_DISCOVERY C7. A rater may add a
# subcategory after a slash, e.g. "accuracy/omission".
CATEGORIES = {"accuracy", "fluency", "terminology", "style", "locale", "other"}

SHEET_FIELDS = ["item_id", "seg_id", "source", "target"]
ANNOTATION_FIELDS = ["item_id", "category", "severity", "note"]
PAIR_SHEET_FIELDS = ["pair_id", "seg_id", "source", "output_1", "output_2"]
PAIR_CHOICE_FIELDS = ["pair_id", "choice", "note"]
PAIR_CHOICES = {"1", "2", "same"}


# ---------------------------------------------------------------- inputs

def load_source(path: Path) -> dict[str, str]:
    return {row["id"]: row["text"] for row in read_jsonl(path)}


def load_targets(path: Path) -> dict[str, str]:
    return {row["id"]: row["target"] for row in read_jsonl(path)}


def parse_systems(specs: list[str]) -> dict[str, dict[str, str]]:
    """["T0=t0.jsonl", ...] -> {"T0": {"S01": "...", ...}, ...}"""
    systems = {}
    for spec in specs:
        name, sep, path = spec.partition("=")
        if not sep or not name or not path:
            raise ValueError(f"--system must look like NAME=path.jsonl, got {spec!r}")
        systems[name] = load_targets(Path(path))
    return systems


def check_coverage(source: dict[str, str], systems: dict[str, dict[str, str]]) -> None:
    for name, targets in systems.items():
        missing = sorted(set(source) - set(targets))
        extra = sorted(set(targets) - set(source))
        if missing or extra:
            raise ValueError(f"{name}: missing segments {missing}, segments not in source {extra}")


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:  # -sig: spreadsheets often add a BOM
        return list(csv.DictReader(f))


def _write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------- step 1: blind MQM sheet

def prepare_mqm(source: dict[str, str], systems: dict[str, dict[str, str]], seed: int) -> tuple[list[dict], dict]:
    check_coverage(source, systems)
    pairs = [(seg_id, name) for seg_id in sorted(source) for name in sorted(systems)]
    random.Random(seed).shuffle(pairs)
    rows, items = [], {}
    for i, (seg_id, name) in enumerate(pairs, start=1):
        item_id = f"M{i:03d}"
        target = systems[name][seg_id].strip()
        rows.append({"item_id": item_id, "seg_id": seg_id, "source": source[seg_id], "target": target})
        items[item_id] = {"seg_id": seg_id, "system": name, "target_sha256": _hash(target)}
    return rows, {"seed": seed, "items": items}


# ---------------------------------------------------------------- step 4: blind pairwise sheet

def prepare_pairs(source: dict[str, str], systems: dict[str, dict[str, str]],
                  comparisons: list[tuple[str, str]], seed: int) -> tuple[list[dict], dict]:
    check_coverage(source, systems)
    rng = random.Random(seed)
    jobs = [(seg_id, a, b) for a, b in comparisons for seg_id in sorted(source)]
    rng.shuffle(jobs)
    rows, pairs = [], {}
    for i, (seg_id, a, b) in enumerate(jobs, start=1):
        first, second = (a, b) if rng.random() < 0.5 else (b, a)
        pair_id = f"P{i:03d}"
        rows.append({"pair_id": pair_id, "seg_id": seg_id, "source": source[seg_id],
                     "output_1": systems[first][seg_id].strip(), "output_2": systems[second][seg_id].strip()})
        pairs[pair_id] = {"seg_id": seg_id, "comparison": f"{a} vs {b}", "output_1": first, "output_2": second}
    return rows, {"seed": seed, "pairs": pairs}


# ---------------------------------------------------------------- step 3: reading ratings

def load_annotations(rows: list[dict], item_ids: set[str], label: str) -> dict[str, list[tuple[str, str]]]:
    """-> {item_id: [(category, severity), ...]}; an empty list means "no errors"."""
    found: dict[str, list[tuple[str, str]]] = defaultdict(list)
    marked_none: set[str] = set()
    for line_no, row in enumerate(rows, start=2):
        item_id = (row.get("item_id") or "").strip()
        severity = (row.get("severity") or "").strip().lower()
        category = (row.get("category") or "").strip().lower()
        where = f"{label} line {line_no}"
        if item_id not in item_ids:
            raise ValueError(f"{where}: unknown item_id {item_id!r}")
        if severity not in SEVERITY_POINTS:
            raise ValueError(f"{where}: severity must be one of {sorted(SEVERITY_POINTS)}, got {severity!r}")
        if severity == "none":
            if category:
                raise ValueError(f"{where}: a 'none' row must have an empty category")
            marked_none.add(item_id)
            found.setdefault(item_id, [])
            continue
        if category.split("/")[0] not in CATEGORIES:
            raise ValueError(f"{where}: category must start with one of {sorted(CATEGORIES)}, got {category!r}")
        found[item_id].append((category, severity))
    both = sorted(i for i in marked_none if found[i])
    if both:
        raise ValueError(f"{label}: items marked 'none' but also given errors: {both}")
    missing = sorted(item_ids - set(found))
    if missing:
        raise ValueError(f"{label}: items not rated (add a 'none' row if they have no errors): {missing}")
    return dict(found)


def load_pair_choices(rows: list[dict], pair_ids: set[str], label: str) -> dict[str, str]:
    choices = {}
    for line_no, row in enumerate(rows, start=2):
        pair_id = (row.get("pair_id") or "").strip()
        choice = (row.get("choice") or "").strip().lower()
        if pair_id not in pair_ids:
            raise ValueError(f"{label} line {line_no}: unknown pair_id {pair_id!r}")
        if choice not in PAIR_CHOICES:
            raise ValueError(f"{label} line {line_no}: choice must be 1, 2 or same, got {choice!r}")
        if pair_id in choices:
            raise ValueError(f"{label} line {line_no}: {pair_id} answered twice")
        choices[pair_id] = choice
    missing = sorted(pair_ids - set(choices))
    if missing:
        raise ValueError(f"{label}: pairs not answered: {missing}")
    return choices


def verify_key(key: dict, source: dict[str, str], systems: dict[str, dict[str, str]]) -> None:
    """The outputs being scored must be exactly the ones that were rated."""
    for item_id, item in key["items"].items():
        target = systems.get(item["system"], {}).get(item["seg_id"])
        if target is None:
            raise ValueError(f"{item_id}: no output for {item['system']} {item['seg_id']}")
        if _hash(target.strip()) != item["target_sha256"]:
            raise ValueError(f"{item_id}: {item['system']} {item['seg_id']} changed after the sheet was made")
    expected = {(seg_id, name) for seg_id in source for name in systems}
    keyed = {(i["seg_id"], i["system"]) for i in key["items"].values()}
    if keyed != expected:
        raise ValueError(f"key does not cover every system x segment: missing {sorted(expected - keyed)}")


# ---------------------------------------------------------------- step 3: scoring

def mqm_by_system(annotations: dict[str, list[tuple[str, str]]], key: dict, source: dict[str, str]) -> dict:
    """Weighted MQM points per 100 source words, per system (lower is better)."""
    words_per_segment = {seg_id: len(text.split()) for seg_id, text in source.items()}
    out: dict[str, dict] = {}
    for item_id, item in key["items"].items():
        row = out.setdefault(item["system"], {"points": 0, "source_words": 0, "errors": defaultdict(int)})
        row["source_words"] += words_per_segment[item["seg_id"]]
        for category, severity in annotations[item_id]:
            row["points"] += SEVERITY_POINTS[severity]
            row["errors"][f"{category.split('/')[0]}:{severity}"] += 1
    for row in out.values():
        row["points_per_100_words"] = 100 * row["points"] / row["source_words"] if row["source_words"] else None
        row["errors"] = dict(sorted(row["errors"].items()))
    return dict(sorted(out.items()))


def _max_severity(errors: list[tuple[str, str]]) -> int:
    return max((SEVERITY_RANK[s] for _, s in errors), default=0)


def mqm_agreement(r1: dict, r2: dict) -> dict:
    """Before discussion. Labels per item: 'has a major or critical error'
    (binary) and the highest severity (ordered; linear-weighted kappa)."""
    items = sorted(r1)
    sev1 = [_max_severity(r1[i]) for i in items]
    sev2 = [_max_severity(r2[i]) for i in items]
    major = SEVERITY_RANK["major"]
    return {
        "has_major_or_critical": binary_summary([s >= major for s in sev1], [s >= major for s in sev2]),
        "highest_severity": {
            "n_items": len(items),
            "raw_agreement": raw_agreement(sev1, sev2),
            "linear_weighted_kappa": linear_weighted_kappa(sev1, sev2, categories=len(SEVERITY_RANK)),
        },
    }


def pair_tally(choices: dict[str, str], key: dict) -> dict:
    """Wins per system for each comparison, with the left/right order undone."""
    out: dict[str, dict] = {}
    for pair_id, choice in choices.items():
        pair = key["pairs"][pair_id]
        row = out.setdefault(pair["comparison"], {"n": 0, "same": 0, "wins": defaultdict(int)})
        row["n"] += 1
        if choice == "same":
            row["same"] += 1
        else:
            row["wins"][pair["output_" + choice]] += 1
    for row in out.values():
        row["wins"] = dict(row["wins"])
    return out


def pair_agreement(p1: dict[str, str], p2: dict[str, str]) -> dict:
    """On the shown labels (1 / 2 / same). Both raters saw the same order."""
    ids = sorted(p1)
    a, b = [p1[i] for i in ids], [p2[i] for i in ids]
    return {"n_items": len(ids), "raw_agreement": raw_agreement(a, b), "kappa": cohen_kappa(a, b)}


def chrf_by_system(systems: dict[str, dict[str, str]], reference: dict[str, str]) -> dict:
    out = {}
    for name, targets in sorted(systems.items()):
        seg_ids = sorted(targets)
        out[name] = {
            "corpus_chrf": corpus_chrf([targets[s] for s in seg_ids], [reference[s] for s in seg_ids]),
            "per_segment": {s: round(sentence_chrf(targets[s], reference[s]), 2) for s in seg_ids},
        }
    return out


def digit_compliance(source: dict[str, str], systems: dict[str, dict[str, str]]) -> dict:
    """Share of source numbers that appear as digits (Western or Tamil) in the
    output, as ADR 0008 instructs. Uses the same number reading as the checks."""
    out = {}
    for name, targets in sorted(systems.items()):
        expected = found = 0
        for seg_id, text in source.items():
            wanted = source_numbers(text)
            got, _ = target_numbers(targets[seg_id], stems=[])
            expected += sum(wanted.values())
            found += sum((wanted & got).values())
        out[name] = {"numbers_in_source": expected, "found_as_digits": found,
                     "rate": found / expected if expected else None}
    return out


def hard_checks_by_system(source: dict[str, str], systems: dict[str, dict[str, str]], checkset: CheckSet) -> dict:
    out = {}
    for name, targets in sorted(systems.items()):
        counts: dict[str, int] = defaultdict(int)
        for seg_id, text in source.items():
            counts[check_segment(seg_id, text, targets[seg_id], checkset).overall] += 1
        n = len(source)
        out[name] = {"pass_rate": counts[PASS] / n if n else None, "counts": dict(counts)}
    return out


def decide(points: dict[str, float], data_terms: dict, hard_checks: dict) -> dict:
    """Rule 3 over all systems, plus the better T2 and whether it beats T0."""
    trains = {name: data_terms[name]["trains_on_data"] for name in points}
    pass_rate = {name: hard_checks[name]["pass_rate"] for name in points}
    decision = {"rule3": rule3(points, trains, pass_rate)}

    t2 = {name: p for name, p in points.items() if name.startswith("T2")}
    if t2:
        better = rule3(t2, trains, pass_rate)
        decision["better_t2"] = better
        winner = better["winner"]
        if winner:
            t1 = "T1" + winner[2:]  # same provider: T2-G -> T1-G
            decision["suggested_pairs"] = [[winner, "T0"], [winner, t1]] if t1 in points else [[winner, "T0"]]
            if "T0" in points:
                decision["better_t2_beats_t0_beyond_tie_margin"] = points["T0"] - points[winner] > TRANSLATION_TIE_POINTS
    return decision


def tally(source: dict[str, str], reference: dict[str, str], systems: dict[str, dict[str, str]],
          key: dict, r1: dict, r2: dict, agreed: dict | None, checkset: CheckSet, data_terms: dict,
          pairs_key: dict | None = None, p1: dict | None = None, p2: dict | None = None,
          pagreed: dict | None = None) -> dict:
    check_coverage(source, systems)
    check_coverage(source, {"reference": reference})
    verify_key(key, source, systems)
    hard = hard_checks_by_system(source, systems, checkset)
    report = {
        "n_segments": len(source),
        "source_words": sum(len(t.split()) for t in source.values()),
        "mqm_r1": mqm_by_system(r1, key, source),
        "mqm_r2": mqm_by_system(r2, key, source),
        "agreement_before_discussion": mqm_agreement(r1, r2),
        "chrf_vs_r1_reference_supporting_only": chrf_by_system(systems, reference),
        "digit_compliance": digit_compliance(source, systems),
        "hard_checks": hard,
    }
    if agreed is None:
        report["decision"] = "not made: needs the agreed labels (--agreed)"
    else:
        report["mqm_agreed"] = mqm_by_system(agreed, key, source)
        points = {name: row["points_per_100_words"] for name, row in report["mqm_agreed"].items()}
        report["decision"] = decide(points, data_terms, hard)
    if pairs_key is not None:
        report["pairwise_r1"] = pair_tally(p1, pairs_key)
        report["pairwise_r2"] = pair_tally(p2, pairs_key)
        report["pairwise_agreement_before_discussion"] = pair_agreement(p1, p2)
        if pagreed is not None:
            report["pairwise_agreed"] = pair_tally(pagreed, pairs_key)
    return report


# ---------------------------------------------------------------- CLI

def _seed(value: int | None) -> int:
    return value if value is not None else random.SystemRandom().randrange(2**32)


def _write_key(path: Path, key: dict) -> None:
    path.write_text(json.dumps(key, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare-mqm")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--system", action="append", required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seed", type=int)

    p = sub.add_parser("prepare-pairs")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--system", action="append", required=True)
    p.add_argument("--compare", action="append", required=True, help="A:B, e.g. T2-G:T0")
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--seed", type=int)

    p = sub.add_parser("tally")
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--reference", type=Path, required=True)
    p.add_argument("--system", action="append", required=True)
    p.add_argument("--mqm-key", type=Path, required=True)
    p.add_argument("--r1", type=Path, required=True)
    p.add_argument("--r2", type=Path, required=True)
    p.add_argument("--agreed", type=Path)
    p.add_argument("--pairs-key", type=Path)
    p.add_argument("--pairs-r1", type=Path)
    p.add_argument("--pairs-r2", type=Path)
    p.add_argument("--pairs-agreed", type=Path)
    p.add_argument("--data-terms", type=Path, default=DATA_TERMS_FILE)
    p.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    source = load_source(args.source)
    systems = parse_systems(args.system)

    if args.command == "prepare-mqm":
        args.out_dir.mkdir(parents=True, exist_ok=True)
        rows, key = prepare_mqm(source, systems, _seed(args.seed))
        _write_csv(args.out_dir / "mqm_sheet.csv", SHEET_FIELDS, rows)
        _write_csv(args.out_dir / "mqm_annotations_template.csv", ANNOTATION_FIELDS, [])
        _write_key(args.out_dir / "mqm_key.json", key)
        print(f"Wrote {len(rows)} items. Give raters mqm_sheet.csv and the template; NOT mqm_key.json.")
        return

    if args.command == "prepare-pairs":
        comparisons = [tuple(c.split(":", 1)) for c in args.compare]
        if any(len(c) != 2 for c in comparisons):
            parser.error("--compare must look like A:B")
        args.out_dir.mkdir(parents=True, exist_ok=True)
        rows, key = prepare_pairs(source, systems, comparisons, _seed(args.seed))
        _write_csv(args.out_dir / "pairs_sheet.csv", PAIR_SHEET_FIELDS, rows)
        _write_csv(args.out_dir / "pairs_choices_template.csv", PAIR_CHOICE_FIELDS, [])
        _write_key(args.out_dir / "pairs_key.json", key)
        print(f"Wrote {len(rows)} pairs. Give raters pairs_sheet.csv and the template; NOT pairs_key.json.")
        return

    key = json.loads(args.mqm_key.read_text(encoding="utf-8"))
    item_ids = set(key["items"])
    r1 = load_annotations(_read_csv(args.r1), item_ids, "r1")
    r2 = load_annotations(_read_csv(args.r2), item_ids, "r2")
    agreed = load_annotations(_read_csv(args.agreed), item_ids, "agreed") if args.agreed else None

    pairs_key = p1 = p2 = pagreed = None
    if args.pairs_key:
        if not (args.pairs_r1 and args.pairs_r2):
            parser.error("--pairs-key needs --pairs-r1 and --pairs-r2")
        pairs_key = json.loads(args.pairs_key.read_text(encoding="utf-8"))
        pair_ids = set(pairs_key["pairs"])
        p1 = load_pair_choices(_read_csv(args.pairs_r1), pair_ids, "pairs-r1")
        p2 = load_pair_choices(_read_csv(args.pairs_r2), pair_ids, "pairs-r2")
        if args.pairs_agreed:
            pagreed = load_pair_choices(_read_csv(args.pairs_agreed), pair_ids, "pairs-agreed")

    data_terms = json.loads(args.data_terms.read_text(encoding="utf-8"))
    report = tally(source, load_targets(args.reference), systems, key, r1, r2, agreed,
                   CheckSet.load(), data_terms, pairs_key, p1, p2, pagreed)
    changed = changed_since_freeze()
    report["hard_check_rules_frozen"] = changed == []
    if changed != []:
        report["hard_check_warning"] = ("rules never frozen" if changed is None else
                                        "rules changed since the freeze: " + ", ".join(changed)) + \
            "; the hard-check tie-break is provisional"
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
