"""Tamil number words 0–100 → values, for the ADR 0008 number check (ADR 0022, option 4).

STATUS: DRAFT written by the assistant, [UNVERIFIED]. A Tamil-literate rater must review the forms below
(as for ta_number_word_stems.txt).

How it reads a word:
- Exact forms are generated: units, 10–19, the tens, 100, and the fused compounds 21–99. A fused compound
  is the tens' joining form with its final "u" dropped, plus the unit with its first vowel written as a
  vowel sign: இருபத்து + ஐந்து → இருபத்தைந்து (25).
- Two-word compounds such as "இருபத்து மூன்று" (23) or "எழுபத்தி நான்கு" (74) are joined.
- Case endings are accepted only from fixed lists, so a word that merely starts like a number is not read as
  one (பத்திரம் "safe" is not பத்து "10").
- AMBIGUOUS words also mean something else, alone or with an ending: ஒரு "a/one", ஒன்றாக "together",
  ஆறு "six/river", ஏழை "poor person", எட்டு "eight/reach", அஞ்சு "five/fear". Ordinals (மூன்றாவது "third")
  are treated the same way, because the English side may say "third" rather than a number. So the plain unit words for 1, 6, 7 and 8 count
  only where the source has that number; otherwise the check stays UNVERIFIABLE (fail-safe). Compounds such
  as இருபத்தொன்று (21) are not ambiguous.
Anything else that looks like a number (hundreds, thousands, decimals) is left to the stem list, which
makes the check UNVERIFIABLE so a reviewer looks.
"""
import re
import unicodedata
from collections import Counter

UNITS = {
    0: ["பூஜ்ஜியம்", "பூஜ்யம்", "சுழியம்"],
    1: ["ஒன்று", "ஒண்ணு"],
    2: ["இரண்டு", "ரெண்டு"],
    3: ["மூன்று", "மூணு"],
    4: ["நான்கு", "நாலு"],
    5: ["ஐந்து", "அஞ்சு"],
    6: ["ஆறு"],
    7: ["ஏழு"],
    8: ["எட்டு"],
    9: ["ஒன்பது"],
}
TEENS = {
    10: ["பத்து"], 11: ["பதினொன்று", "பதினொண்ணு"], 12: ["பன்னிரண்டு", "பன்னெண்டு"],
    13: ["பதின்மூன்று", "பதிமூன்று", "பதிமூணு"], 14: ["பதினான்கு", "பதினாலு"], 15: ["பதினைந்து", "பதினஞ்சு"],
    16: ["பதினாறு"], 17: ["பதினேழு"], 18: ["பதினெட்டு"], 19: ["பத்தொன்பது"],
}
TENS = {20: "இருபது", 30: "முப்பது", 40: "நாற்பது", 50: "ஐம்பது", 60: "அறுபது", 70: "எழுபது", 80: "எண்பது",
        90: "தொண்ணூறு"}
# Joining forms used before a unit: "-ttu" (standard) and "-tti" (common in speech).
JOINING = {20: ["இருபத்து", "இருபத்தி"], 30: ["முப்பத்து", "முப்பத்தி"], 40: ["நாற்பத்து", "நாற்பத்தி"],
           50: ["ஐம்பத்து", "ஐம்பத்தி"], 60: ["அறுபத்து", "அறுபத்தி"], 70: ["எழுபத்து", "எழுபத்தி"],
           80: ["எண்பத்து", "எண்பத்தி"], 90: ["தொண்ணூற்று", "தொண்ணூற்றி"]}
HUNDRED = ["நூறு"]
AMBIGUOUS_VALUES = (1, 6, 7, 8)  # plain unit words with common non-number meanings
AMBIGUOUS = {"ஒரு": 1, "அஞ்சு": 5, **{w: v for v in AMBIGUOUS_VALUES for w in UNITS[v]}}  # அஞ்சு also "fear"
ORDINAL_ENDING = "ாவது"  # மூன்றாவது "third": counts only where the source has that number (it may be an ordinal)

VOWEL_SIGN = {"அ": "", "ஆ": "ா", "இ": "ி", "ஈ": "ீ", "உ": "ு", "ஊ": "ூ", "எ": "ெ", "ஏ": "ே", "ஐ": "ை",
              "ஒ": "ொ", "ஓ": "ோ"}
U_SIGN = "ு"
# Endings accepted after a full form, and after a form whose final "u" is dropped before a vowel.
FULL_FORM_ENDINGS = {"", "க்கு", "க்குப்", "க்கும்", "க்குள்", "ம்", "டன்", "தான்", "ே"}
U_DROPPED_ENDINGS = {"ை", "ையும்", "ைப்", "ைக்", "ைத்", "ால்", "ாக", "ாகும்", "ாவது", "ாம்", "ில்", "ிலும்",
                     "ின்", "ுக்கு", "ுக்குப்", "ுக்கும்", "ோடு", "ுடன்", "ும்"}
WORD_RE = re.compile(r"[஀-௿]+")


def _nfc(text):
    return unicodedata.normalize("NFC", text)


def _fuse(joining, unit):
    """இருபத்து + ஐந்து → இருபத்தைந்து; இருபத்து + மூன்று → இருபத்துமூன்று."""
    sign = VOWEL_SIGN.get(unit[0])
    if sign is None:  # the unit starts with a consonant: plain concatenation
        return joining + unit
    base = joining[:-1] if joining.endswith(U_SIGN) or joining.endswith("ி") else joining
    return base + sign + unit[1:]


def _build_forms():
    forms = {}
    for value, words in {**UNITS, **TEENS}.items():
        for w in words:
            forms[_nfc(w)] = value
    for value, word in TENS.items():
        forms[_nfc(word)] = value
    for w in HUNDRED:
        forms[_nfc(w)] = 100
    for tens, joinings in JOINING.items():
        for joining in joinings:
            for unit_value, unit_words in UNITS.items():
                if unit_value == 0:
                    continue
                for unit in unit_words:
                    forms[_nfc(_fuse(joining, unit))] = tens + unit_value
    for word in AMBIGUOUS:
        forms.pop(_nfc(word), None)  # handled separately
    return forms


FORMS = _build_forms()
JOINING_FORMS = {_nfc(j): tens for tens, js in JOINING.items() for j in js}


def _read_word(word):
    """Value of one word (with an accepted ending), or None."""
    if word in FORMS:
        return FORMS[word]
    for form in sorted(FORMS, key=len, reverse=True):
        if word.startswith(form) and word[len(form):] in FULL_FORM_ENDINGS:
            return FORMS[form]
        if form.endswith(U_SIGN):
            stem = form[:-1]
            if word.startswith(stem) and word[len(stem):] in U_DROPPED_ENDINGS:
                return FORMS[form]
    return None


def _read_ambiguous(word):
    for form, value in sorted(AMBIGUOUS.items(), key=lambda kv: len(kv[0]), reverse=True):
        if word == form or (word.startswith(form) and word[len(form):] in FULL_FORM_ENDINGS):
            return value
        if form.endswith(U_SIGN) and word.startswith(form[:-1]) and word[len(form) - 1:] in U_DROPPED_ENDINGS:
            return value
    return None


def parse(text):
    """Return (values: Counter, ambiguous: list[int], consumed: set of word indexes) for Tamil text."""
    words = WORD_RE.findall(_nfc(text or ""))
    values, ambiguous, consumed = Counter(), [], set()
    i = 0
    while i < len(words):
        word = words[i]
        if word in JOINING_FORMS and i + 1 < len(words):
            unit = _read_word(words[i + 1])
            if unit is None:  # "இருபத்து ஒன்று": an ambiguous unit is unambiguous after a joining form
                unit = _read_ambiguous(words[i + 1])
            if unit is not None and 1 <= unit <= 9:
                values[JOINING_FORMS[word] + unit] += 1
                consumed.update({i, i + 1})
                i += 2
                continue
        value = _read_word(word)
        if value is not None and ORDINAL_ENDING in word:
            ambiguous.append(value)
            consumed.add(i)
        elif value is not None:
            values[value] += 1
            consumed.add(i)
        else:
            amb = _read_ambiguous(word)
            if amb is not None:
                ambiguous.append(amb)
                consumed.add(i)
        i += 1
    return values, ambiguous, consumed


def words_of(text):
    return WORD_RE.findall(_nfc(text or ""))
