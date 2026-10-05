"""Test-only lexicon data. NOT the spike lexicon: the real Tamil forms come
from R1/R2 (spike/data/). These forms exist only to exercise the matching."""

from hlspike.checks import CheckSet
from hlspike.numbers import load_tamil_number_stems

UNITS = [
    {"canonical": "ml", "en_forms": ["millilitre", "millilitres", "ml"], "latin_target_forms": ["mL"], "ta_forms": ["மில்லி"]},
    {"canonical": "L", "en_forms": ["litre", "litres"], "latin_target_forms": ["L"], "ta_forms": ["லிட்டர்"]},
    {"canonical": "mg", "en_forms": ["milligram", "milligrams", "mg"], "latin_target_forms": [], "ta_forms": []},
]
GLOSSARY = [
    {"id": "zinc", "en_forms": ["zinc"], "ta_forms": ["துத்தநாகம்"], "ta_stem": "துத்தநாக", "do_not_translate": False},
    {"id": "ors", "en_forms": ["ORS"], "ta_forms": [], "ta_stem": "", "do_not_translate": True},
    {"id": "sachet", "en_forms": ["sachet"], "ta_forms": [], "ta_stem": "", "do_not_translate": False},
]


def checkset() -> CheckSet:
    return CheckSet(UNITS, GLOSSARY, load_tamil_number_stems())
