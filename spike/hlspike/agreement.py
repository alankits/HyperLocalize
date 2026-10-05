"""Agreement between two raters (SPIKE_PLAN M2).

The plan asks for raw % agreement and the label's prevalence alongside
Cohen's kappa, because kappa is unstable when a label is rare: with very few
positives, two raters can agree on 95% of items and still get kappa near 0.
So every function here returns all three, never kappa alone.
"""

from collections import Counter


def raw_agreement(a: list, b: list) -> float | None:
    _same_length(a, b)
    return sum(x == y for x, y in zip(a, b)) / len(a) if a else None


def cohen_kappa(a: list, b: list) -> float | None:
    """Unweighted kappa. None when chance agreement is 1 (both raters gave one
    identical label to everything), where kappa is undefined."""
    _same_length(a, b)
    if not a:
        return None
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    count_a, count_b = Counter(a), Counter(b)
    expected = sum(count_a[k] * count_b[k] for k in count_a) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def linear_weighted_kappa(a: list[int], b: list[int], categories: int) -> float | None:
    """Weighted kappa for ordered labels 0..categories-1 with LINEAR weights:
    disagreeing by one step (minor vs major) costs less than by two.
    Linear (not quadratic) weights were chosen by the assistant on 2026-10-05,
    before any data existed; the plan only says "weighted kappa"."""
    _same_length(a, b)
    if not a:
        return None
    n = len(a)

    def weight(i: int, j: int) -> float:
        return 1 - abs(i - j) / (categories - 1)

    observed = sum(weight(x, y) for x, y in zip(a, b)) / n
    count_a, count_b = Counter(a), Counter(b)
    expected = sum(weight(i, j) * count_a[i] * count_b[j]
                   for i in range(categories) for j in range(categories)) / (n * n)
    return None if expected == 1 else (observed - expected) / (1 - expected)


def binary_summary(a: list[bool], b: list[bool]) -> dict:
    """Raw agreement, prevalence (share of all labels from both raters that are
    positive) and kappa, for a yes/no label."""
    _same_length(a, b)
    return {
        "n_items": len(a),
        "raw_agreement": raw_agreement(a, b),
        "prevalence": (sum(a) + sum(b)) / (2 * len(a)) if a else None,
        "kappa": cohen_kappa(a, b),
    }


def _same_length(a: list, b: list) -> None:
    if len(a) != len(b):
        raise ValueError(f"raters labelled different numbers of items ({len(a)} vs {len(b)})")
