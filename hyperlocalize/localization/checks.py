"""Rule-based critical-content checks (ADR 0008), language-neutral with language packs.

Ported from the spike tooling (spike/hlspike), generalised so that the framework is not
tied to one language pair:
- a SOURCE pack reads numbers in the source language (MVP: English);
- a TARGET pack normalises numbers in the target language (MVP: Tamil) and lists the
  number-word stems that make a result UNVERIFIABLE (fail-safe);
- units come from a lexicon with forms per language; glossary terms come from the project.

A FAIL or UNVERIFIABLE hard check blocks approval until fixed or overridden with a written
reason (ADR 0008). Negation and meaning reversal are NOT rule-checked: they go to the AI
flagger and the human reviewer. A target language with no pack gives UNVERIFIABLE numbers
(never a silent PASS).
"""
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

PASS, FAIL, UNVERIFIABLE = "PASS", "FAIL", "UNVERIFIABLE"
LEXICON_DIR = Path(__file__).parent / "lexicons"
LATIN_SHARE_LIMIT = 0.5
CHARS_PER_SECOND_BUDGET = 18  # TARGET: a working subtitle reading-speed budget, not a measured value

# ----------------------------------------------------------------- English source numbers

SMALL = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}
BIG_SCALES = {"thousand": 1_000, "lakh": 100_000, "million": 1_000_000, "crore": 10_000_000}
FREQUENCY = {"once": 1, "twice": 2}


def parse_number_words(words, start):
    """Read one English number written in words at words[start]. Returns (value, end) or None."""
    total = current = 0
    i, used = start, False
    while i < len(words):
        word = words[i]
        if word in SMALL:
            ones_tens = current % 100
            if ones_tens != 0 and not (ones_tens % 10 == 0 and ones_tens >= 20 and SMALL[word] < 10):
                break
            current += SMALL[word]
        elif word in TENS:
            if current % 100 != 0:
                break
            current += TENS[word]
        elif word == "hundred":
            if not used or current == 0 or current >= 100:
                break
            current *= 100
        elif word in BIG_SCALES:
            if not used:
                break
            total += max(current, 1) * BIG_SCALES[word]
            current = 0
        elif word == "and" and used and i + 1 < len(words) and (words[i + 1] in SMALL or words[i + 1] in TENS):
            if current % 100 != 0 or current == 0 and total == 0:
                break
        else:
            break
        used = True
        i += 1
    return (total + current, i) if used else None


DIGIT_RUN_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")


def _digit_run_values(run):
    integer_part, _, decimals = run.partition(".")
    groups = integer_part.split(",")
    if len(groups) > 1:
        western = 1 <= len(groups[0]) <= 3 and all(len(g) == 3 for g in groups[1:])
        indian = 1 <= len(groups[0]) <= 2 and all(len(g) == 2 for g in groups[1:-1]) and len(groups[-1]) == 3
        if not (western or indian):
            values = [Decimal(g) for g in groups[:-1]]
            values.append(Decimal(groups[-1] + ("." + decimals if decimals else "")))
            return values
    return [Decimal("".join(groups) + ("." + decimals if decimals else ""))]


def _digit_values(text):
    values = TIME_RE.findall(text)
    text = TIME_RE.sub(" ", text)
    for run in DIGIT_RUN_RE.findall(text):
        values.extend(_digit_run_values(run))
    return values, DIGIT_RUN_RE.sub(" ", text)


def english_source_numbers(text):
    values, rest = _digit_values(text)
    words = re.findall(r"[a-z]+", rest.lower())
    i = 0
    while i < len(words):
        if words[i] in FREQUENCY:
            values.append(Decimal(FREQUENCY[words[i]]))
            i += 1
            continue
        parsed = parse_number_words(words, i)
        if parsed is None:
            i += 1
        else:
            value, i = parsed
            values.append(Decimal(value))
    return Counter(values)


SOURCE_PACKS = {"en": english_source_numbers}

# ----------------------------------------------------------------- target packs


@dataclass
class TargetPack:
    language: str
    script_is_latin: bool
    digit_map: dict = field(default_factory=dict)  # native digit → ASCII digit
    non_positional_numerals: str = ""
    word_re: str = r"[^\W\d_]+"
    stems_file: str = ""

    @property
    def stems(self):
        return _load_stems(self.stems_file) if self.stems_file else []


@lru_cache(maxsize=None)
def _load_stems(name):
    lines = (LEXICON_DIR / name).read_text(encoding="utf-8").splitlines()
    return tuple(ln.split("#")[0].strip() for ln in lines if ln.split("#")[0].strip())


TARGET_PACKS = {
    # MVP target language (Q3). The stems list is a DRAFT until a Tamil rater reviews it.
    "ta": TargetPack("ta", False, dict(zip("௦௧௨௩௪௫௬௭௮௯", "0123456789")), "௰௱௲", r"[஀-௿]+", "ta_number_word_stems.txt"),
}


def language_of(locale):
    return (locale or "").split("-")[0].lower()


def target_numbers(text, pack):
    if pack.digit_map:
        text = text.translate(str.maketrans(pack.digit_map))
    values, rest = _digit_values(text)
    reasons = [f"non-positional numeral '{ch}'" for ch in pack.non_positional_numerals if ch in rest]
    for word in re.findall(pack.word_re, rest):
        stem = next((s for s in pack.stems if word.startswith(s)), None)
        if stem:
            reasons.append(f"possible number word '{word}' (stem '{stem}')")
    return Counter(values), reasons


def _show(counter):
    return ", ".join(str(v) for v in sorted(counter.elements(), key=str))


def check_numbers(source, target, source_lang, target_lang):
    source_reader = SOURCE_PACKS.get(source_lang)
    pack = TARGET_PACKS.get(target_lang)
    if source_reader is None or pack is None:
        return UNVERIFIABLE, [f"no number rules for {source_lang} → {target_lang} yet"]
    expected = source_reader(source)
    found, unverifiable = target_numbers(target, pack)
    missing, extra = expected - found, found - expected
    details = []
    if extra:
        details.append(f"numbers not in source: {_show(extra)}")
        if missing:
            details.append(f"missing from target: {_show(missing)}")
        return FAIL, details + unverifiable
    if unverifiable:
        if missing:
            details.append(f"not found as digits (may be written as words): {_show(missing)}")
        return UNVERIFIABLE, details + unverifiable
    if missing:
        return FAIL, [f"missing from target: {_show(missing)}"]
    return PASS, []


# ----------------------------------------------------------------- units and glossary

@lru_cache(maxsize=None)
def unit_lexicon():
    return json.loads((LEXICON_DIR / "units.json").read_text(encoding="utf-8"))["entries"]


def _latin_present(text, form):
    flags = 0 if len(form) == 1 else re.IGNORECASE
    return re.search(rf"(?<![A-Za-z]){re.escape(form)}(?![A-Za-z])", text, flags) is not None


def _target_present(text, form, pack):
    if " " in form:
        return form in text
    word_re = pack.word_re if pack else r"[^\W\d_]+"
    return any(word.startswith(form) for word in re.findall(word_re, text))


def check_units(source, target, source_lang, target_lang, conversions=()):
    """Every source unit must appear in the target, and the target must not add one.
    A declared audience conversion (ADR 0008) cannot be value-checked yet: UNVERIFIABLE (fail-safe)."""
    pack = TARGET_PACKS.get(target_lang)
    converted_from = {str(c.get("from", "")).lower() for c in conversions or []}
    details, unverifiable = [], []
    for unit in unit_lexicon():
        src_forms = unit["source"].get(source_lang, [])
        tgt_forms = unit["target"].get(target_lang, [])
        in_source = any(_latin_present(source, f) for f in src_forms)
        in_target = any(_latin_present(target, f) for f in src_forms + unit["latin_target"]) or any(
            _target_present(target, f, pack) for f in tgt_forms
        )
        if in_source and not in_target:
            if unit["canonical"].lower() in converted_from:
                unverifiable.append(f"unit '{unit['canonical']}' may have been converted (declared); check the value")
            else:
                note = "" if tgt_forms else " (no target-language forms in the lexicon yet)"
                details.append(f"unit '{unit['canonical']}' missing from target{note}")
        elif in_target and not in_source:
            details.append(f"unit '{unit['canonical']}' in target but not in source")
    if details:
        return FAIL, details + unverifiable
    return (UNVERIFIABLE, unverifiable) if unverifiable else (PASS, [])


def check_glossary(source, target, glossary, target_lang):
    """glossary: dicts with source_term, target_term, accepted_forms, do_not_translate.
    A term with no accepted target forms gives UNVERIFIABLE, never PASS."""
    pack = TARGET_PACKS.get(target_lang)
    failures, unverifiable = [], []
    for entry in glossary:
        if not _latin_present(source, entry["source_term"]):
            continue
        accepted = [f for f in [entry.get("target_term", "")] + list(entry.get("accepted_forms") or []) if f]
        if entry.get("do_not_translate"):
            ok = _latin_present(target, entry["source_term"]) or any(_target_present(target, f, pack) for f in accepted)
        elif not accepted:
            unverifiable.append(f"glossary term '{entry['source_term']}' has no accepted target forms yet")
            continue
        else:
            ok = any(_target_present(target, f, pack) or _latin_present(target, f) for f in accepted)
        if not ok:
            failures.append(f"glossary term '{entry['source_term']}' not found in an accepted form")
    if failures:
        return FAIL, failures + unverifiable
    return (UNVERIFIABLE, unverifiable) if unverifiable else (PASS, [])


def check_structure(source, target, target_lang, duration_ms=None):
    if not target.strip():
        return FAIL, ["target is empty"]
    details = []
    if " ".join(target.lower().split()) == " ".join(source.lower().split()):
        details.append("target is the same as the source (untranslated)")
    pack = TARGET_PACKS.get(target_lang)
    if pack is not None and not pack.script_is_latin:
        letters = [ch for ch in target if ch.isalpha()]
        latin = sum(1 for ch in letters if ch.isascii())
        if letters and latin / len(letters) > LATIN_SHARE_LIMIT:
            details.append(f"target is mostly Latin script ({latin}/{len(letters)} letters)")
    if duration_ms:
        budget = int(duration_ms / 1000 * CHARS_PER_SECOND_BUDGET) + 10
        if len(target) > budget:
            details.append(f"target is {len(target)} characters; the timing budget is about {budget}")
    return (FAIL, details) if details else (PASS, [])


def run_hard_checks(source, target, *, source_lang, target_locale, glossary, conversions=(), duration_ms=None):
    """Return {check_type: (status, details)} for one segment."""
    target_lang = language_of(target_locale)
    return {
        "structure": check_structure(source, target, target_lang, duration_ms),
        "numbers": check_numbers(source, target, source_lang, target_lang),
        "units": check_units(source, target, source_lang, target_lang, conversions),
        "glossary": check_glossary(source, target, glossary, target_lang),
    }
