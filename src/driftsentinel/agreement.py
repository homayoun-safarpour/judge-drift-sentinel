"""Agreement metrics between two categorical labelings.

Everything operates on dicts mapping item id -> label, so callers never
have to align two lists by position. Only ids present in BOTH labelings
are compared; the caller decides whether missing ids are an error
(anchor validation does exactly that).
"""

from __future__ import annotations

from collections import Counter


def _shared_ids(a: dict[str, str], b: dict[str, str]) -> list[str]:
    shared = sorted(set(a) & set(b))
    if not shared:
        raise ValueError("no shared item ids between the two labelings")
    return shared


def observed_agreement(a: dict[str, str], b: dict[str, str]) -> float:
    """Fraction of shared items on which both labelings give the same label."""
    shared = _shared_ids(a, b)
    same = sum(1 for i in shared if a[i] == b[i])
    return same / len(shared)


def cohen_kappa(a: dict[str, str], b: dict[str, str]) -> float:
    """Cohen's kappa: agreement above what label frequencies alone would produce.

    1.0 is perfect agreement, 0.0 is chance-level, negative is worse than
    chance. When expected chance agreement is 1.0 (both raters use a single
    label), kappa is defined here as 1.0 on full agreement and 0.0 otherwise.
    """
    shared = _shared_ids(a, b)
    n = len(shared)
    p_observed = observed_agreement(a, b)

    freq_a = Counter(a[i] for i in shared)
    freq_b = Counter(b[i] for i in shared)
    labels = set(freq_a) | set(freq_b)
    p_expected = sum((freq_a[lbl] / n) * (freq_b[lbl] / n) for lbl in labels)

    if p_expected >= 1.0:
        return 1.0 if p_observed == 1.0 else 0.0
    return (p_observed - p_expected) / (1.0 - p_expected)


def flip_rate(a: dict[str, str], b: dict[str, str]) -> float:
    """Fraction of shared items whose label differs between the two labelings."""
    return 1.0 - observed_agreement(a, b)
