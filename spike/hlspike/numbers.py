"""ADR 0008 number check (MVP scope).

Source (English): digits, decimals, Western grouping (1,000), times (10:30),
ranges (each end counts), English number words, and "once"/"twice".
Target (Tamil): Western digits (Western 1,000,000 or Indian 10,00,000 grouping,
decimals) and Tamil digits ௦-௯. Tamil number WORDS and the non-positional
numerals ௰ ௱ ௲ are NOT parsed: they make the result UNVERIFIABLE (fail-safe).

The two sides are compared as multisets: same values, same counts.
"""

import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from . import DATA_DIR
from .english_numbers import FREQUENCY, parse_number_words

PASS, FAIL, UNVERIFIABLE = "PASS", "FAIL", "UNVERIFIABLE"

TAMIL_DIGITS = str.maketrans("௦௧௨௩௪௫௬௭௮௯", "0123456789")
NON_POSITIONAL_NUMERALS = "௰௱௲"  # 10, 100, 1000
DIGIT_RUN_RE = re.compile(r"\d+(?:,\d+)*(?:\.\d+)?")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")
TAMIL_WORD_RE = re.compile(r"[஀-௿]+")
STEMS_FILE = DATA_DIR / "ta_number_word_stems.txt"


def load_tamil_number_stems(path: Path = STEMS_FILE) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.split("#")[0].strip() for line in lines if line.split("#")[0].strip()]


def _digit_run_values(run: str) -> list[Decimal]:
    """'1,00,000' -> [100000]; '1,000.5' -> [1000.5]; '5,10' (a list) -> [5, 10]."""
    integer_part, _, decimals = run.partition(".")
    groups = integer_part.split(",")
    if len(groups) > 1:
        western = 1 <= len(groups[0]) <= 3 and all(len(g) == 3 for g in groups[1:])
        indian = 1 <= len(groups[0]) <= 2 and all(len(g) == 2 for g in groups[1:-1]) and len(groups[-1]) == 3
        if not (western or indian):
            # Not a grouped number: treat the commas as separators between numbers.
            values = [Decimal(g) for g in groups[:-1]]
            values.append(Decimal(groups[-1] + ("." + decimals if decimals else "")))
            return values
    return [Decimal("".join(groups) + ("." + decimals if decimals else ""))]


def _digit_values(text: str) -> tuple[list, str]:
    """Extract times and digit numbers. Returns (values, text with them removed)."""
    values: list = TIME_RE.findall(text)  # times stay as strings, e.g. "10:30"
    text = TIME_RE.sub(" ", text)
    for run in DIGIT_RUN_RE.findall(text):
        values.extend(_digit_run_values(run))
    return values, DIGIT_RUN_RE.sub(" ", text)


def source_numbers(text: str) -> Counter:
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


def target_numbers(text: str, stems: list[str]) -> tuple[Counter, list[str]]:
    """Return (digit values found, reasons the target is UNVERIFIABLE)."""
    values, rest = _digit_values(text.translate(TAMIL_DIGITS))
    reasons = [f"non-positional Tamil numeral '{ch}'" for ch in NON_POSITIONAL_NUMERALS if ch in rest]
    for word in TAMIL_WORD_RE.findall(rest):
        stem = next((s for s in stems if word.startswith(s)), None)
        if stem:
            reasons.append(f"possible Tamil number word '{word}' (stem '{stem}')")
    return Counter(values), reasons


def check_numbers(source: str, target: str, stems: list[str]) -> tuple[str, list[str]]:
    expected = source_numbers(source)
    found, unverifiable_reasons = target_numbers(target, stems)
    missing = expected - found
    extra = found - expected
    details = []
    if extra:
        # A digit the source does not have cannot be explained by number words.
        details.append(f"numbers not in source: {_show(extra)}")
        if missing:
            details.append(f"missing from target: {_show(missing)}")
        return FAIL, details + unverifiable_reasons
    if unverifiable_reasons:
        if missing:
            details.append(f"not found as digits (may be written as words): {_show(missing)}")
        return UNVERIFIABLE, details + unverifiable_reasons
    if missing:
        return FAIL, [f"missing from target: {_show(missing)}"]
    return PASS, []


def _show(counter: Counter) -> str:
    return ", ".join(str(v) for v in sorted(counter.elements(), key=str))
