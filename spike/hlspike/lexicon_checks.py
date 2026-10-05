"""ADR 0008 unit and glossary checks.

Both use rater-maintained lexicons in spike/data/. Tamil forms are filled in by
R1/R2, not from memory (ADR 0008). Tamil words are matched as prefixes so that
inflected forms (case suffixes) still match.
"""

import json
import re
from pathlib import Path

from . import DATA_DIR

PASS, FAIL, UNVERIFIABLE = "PASS", "FAIL", "UNVERIFIABLE"
TAMIL_WORD_RE = re.compile(r"[஀-௿]+")


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def _latin_present(text: str, form: str) -> bool:
    # One-letter forms such as "L" are matched case-sensitively; others are not.
    flags = 0 if len(form) == 1 else re.IGNORECASE
    return re.search(rf"(?<![A-Za-z]){re.escape(form)}(?![A-Za-z])", text, flags) is not None


def _tamil_present(text: str, form: str) -> bool:
    if " " in form:
        return form in text
    return any(word.startswith(form) for word in TAMIL_WORD_RE.findall(text))


def _any_form(text: str, latin_forms: list[str], tamil_forms: list[str]) -> bool:
    return any(_latin_present(text, f) for f in latin_forms) or any(_tamil_present(text, f) for f in tamil_forms)


# ------------------------------------------------------------------- units

def check_units(source: str, target: str, units: list[dict]) -> tuple[str, list[str]]:
    """Every source unit must appear in the target, and the target must not add
    a unit the source does not have. Unit conversion is not accepted in the
    spike (the audience profile that would allow it does not exist yet)."""
    details = []
    for unit in units:
        in_source = any(_latin_present(source, f) for f in unit["en_forms"])
        in_target = _any_form(target, unit["en_forms"] + unit["latin_target_forms"], unit["ta_forms"])
        if in_source and not in_target:
            note = "" if unit["ta_forms"] else " (lexicon has no Tamil forms yet)"
            details.append(f"unit '{unit['canonical']}' missing from target{note}")
        elif in_target and not in_source:
            details.append(f"unit '{unit['canonical']}' in target but not in source")
    return (FAIL, details) if details else (PASS, [])


# ---------------------------------------------------------------- glossary

def check_glossary(source: str, target: str, glossary: list[dict]) -> tuple[str, list[str]]:
    """For each glossary term in the source, the target must contain an accepted
    Tamil form, or the stem followed by any suffix. Do-not-translate terms must
    appear unchanged or as a listed transliteration. An entry with no Tamil
    forms yet gives UNVERIFIABLE, never PASS."""
    failures, unverifiable = [], []
    for entry in glossary:
        if not any(_latin_present(source, f) for f in entry["en_forms"]):
            continue
        accepted = list(entry["ta_forms"])
        if entry.get("ta_stem"):
            accepted.append(entry["ta_stem"])
        if entry.get("do_not_translate"):
            ok = _any_form(target, entry["en_forms"], accepted)
        elif not accepted:
            unverifiable.append(f"glossary term '{entry['id']}' has no accepted Tamil forms yet")
            continue
        else:
            ok = any(_tamil_present(target, f) for f in accepted)
        if not ok:
            failures.append(f"glossary term '{entry['id']}' not found in an accepted form")
    if failures:
        return FAIL, failures + unverifiable
    if unverifiable:
        return UNVERIFIABLE, unverifiable
    return PASS, []
