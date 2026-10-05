"""Read English number words ("twenty four", "one hundred and five") as integers.

Used by:
- the M1 ASR scorer, so that "fifty" and "50" count as the same token;
- the source side of the ADR 0008 number check ("give two sachets").

Input is a list of lower-case words. Hyphenated numbers ("twenty-four") must
already be split into separate words by the tokenizer.
"""

SMALL = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
    "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
}
TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
# Scales above a hundred close a block: "two thousand five" = 2000 + 5.
BIG_SCALES = {"thousand": 1_000, "lakh": 100_000, "million": 1_000_000, "crore": 10_000_000}

# Frequency words that carry a number ("once a day"). Only the ADR 0008 source
# check uses these; the ASR scorer keeps "once" as a word (TEST_SCRIPT §2b).
FREQUENCY = {"once": 1, "twice": 2}


def parse_number_words(words: list[str], start: int) -> tuple[int, int] | None:
    """Try to read one number written in words, starting at words[start].

    Returns (value, end), where end is the index just after the last word
    used, or None if words[start] does not begin a number.
    "one two" is read as two separate numbers, not as 3.
    """
    total = 0      # finished blocks (thousands, lakhs, ...)
    current = 0    # the block being built (0-999)
    i = start
    used = False

    while i < len(words):
        word = words[i]
        if word in SMALL:
            # Allowed at the start of a block, or after a tens word ("twenty four").
            ones_and_tens = current % 100
            if ones_and_tens != 0 and not (ones_and_tens % 10 == 0 and ones_and_tens >= 20 and SMALL[word] < 10):
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
            # British "one hundred and five": skip "and" only inside a number.
            if current % 100 != 0 or current == 0 and total == 0:
                break
        else:
            break
        used = True
        i += 1

    if not used:
        return None
    return total + current, i
