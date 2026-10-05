"""chrF (Popović 2015), written to match sacreBLEU's default settings.

Defaults copied from sacreBLEU 2.x: character n-grams of order 1-6, no word
n-grams, beta = 2, whitespace removed before counting, no eps smoothing.
Corpus chrF sums the n-gram statistics over all segments first; it is NOT
the mean of sentence scores.

One difference: both texts are Unicode NFC-normalised first, so that the same
Tamil letter typed two ways (for example ொ as one or two code points) counts
as the same characters. sacreBLEU does not do this. On NFC input the two give
the same score (checked in tests/test_translation_eval.py when sacreBLEU is
installed; it is not a dependency).

n-grams are over Unicode code points, not Tamil letters (grapheme clusters).
That is also what sacreBLEU does, so scores stay comparable.

chrF is SUPPORTING evidence only (SPIKE_PLAN M2): the reference is R1's, and
R1 also rates.
"""

import unicodedata
from collections import Counter

CHAR_ORDER = 6
BETA = 2


def _char_ngrams(text: str, n: int) -> Counter:
    chars = "".join(unicodedata.normalize("NFC", text).split())
    return Counter(chars[i:i + n] for i in range(len(chars) - n + 1))


def segment_stats(hypothesis: str, reference: str) -> list[tuple[int, int, int]]:
    """For each order n: (hypothesis n-grams, reference n-grams, matching n-grams)."""
    stats = []
    for n in range(1, CHAR_ORDER + 1):
        hyp, ref = _char_ngrams(hypothesis, n), _char_ngrams(reference, n)
        stats.append((sum(hyp.values()), sum(ref.values()), sum((hyp & ref).values())))
    return stats


def score_from_stats(stats: list[tuple[int, int, int]]) -> float:
    """Average precision and recall over the orders that exist in both texts,
    then take the F-beta score (sacreBLEU's default path). Range 0-100."""
    precisions, recalls = [], []
    for n_hyp, n_ref, n_match in stats:
        if n_hyp > 0 and n_ref > 0:
            precisions.append(n_match / n_hyp)
            recalls.append(n_match / n_ref)
    if not precisions:
        return 0.0
    precision = sum(precisions) / len(precisions)
    recall = sum(recalls) / len(recalls)
    if precision + recall == 0:
        return 0.0
    factor = BETA ** 2
    return 100 * (1 + factor) * precision * recall / (factor * precision + recall)


def sentence_chrf(hypothesis: str, reference: str) -> float:
    return score_from_stats(segment_stats(hypothesis, reference))


def corpus_chrf(hypotheses: list[str], references: list[str]) -> float:
    if len(hypotheses) != len(references):
        raise ValueError("need one reference per hypothesis")
    totals = [[0, 0, 0] for _ in range(CHAR_ORDER)]
    for hyp, ref in zip(hypotheses, references):
        for total, stat in zip(totals, segment_stats(hyp, ref)):
            for i in range(3):
                total[i] += stat[i]
    return score_from_stats([tuple(t) for t in totals])
