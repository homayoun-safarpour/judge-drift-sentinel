"""Agreement metrics between two categorical labelings.

Everything operates on dicts mapping item id -> label, so callers never
have to align two lists by position. Only ids present in BOTH labelings
are compared; the caller decides whether missing ids are an error
(anchor validation does exactly that).

Unweighted Cohen's kappa treats every disagreement the same (pass/fail or
any categorical labels). Weighted kappa is for ordinal rubrics (e.g. 0-3):
near misses cost less than far misses under linear or quadratic weights.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

WEIGHT_SCHEMES = frozenset({"none", "linear", "quadratic"})


@dataclass(frozen=True)
class KappaConfig:
    """How to score agreement: unweighted (default) or ordinal weighted kappa."""

    weights: str = "none"
    levels: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        scheme = (self.weights or "none").lower()
        if scheme not in WEIGHT_SCHEMES:
            raise ValueError(
                f"kappa weights must be one of {sorted(WEIGHT_SCHEMES)}, got {self.weights!r}"
            )
        object.__setattr__(self, "weights", scheme)
        if self.levels is not None:
            object.__setattr__(self, "levels", tuple(int(x) for x in self.levels))


DEFAULT_KAPPA = KappaConfig()


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


def _parse_ordinal(label: str) -> int:
    text = str(label).strip()
    try:
        value = int(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"ordinal kappa requires integer labels (e.g. 0-3), got {label!r}"
        ) from exc
    if str(value) != text:
        raise ValueError(
            f"ordinal kappa requires integer labels (e.g. 0-3), got {label!r}"
        )
    return value


def _resolve_levels(
    values_a: Sequence[int],
    values_b: Sequence[int],
    levels: Sequence[int] | None,
) -> tuple[int, ...]:
    if levels is None:
        resolved = tuple(sorted(set(values_a) | set(values_b)))
    else:
        resolved = tuple(sorted(int(x) for x in levels))
        if len(resolved) != len(set(resolved)):
            raise ValueError("kappa levels must be unique integers")
        unknown = (set(values_a) | set(values_b)) - set(resolved)
        if unknown:
            bad = ", ".join(str(x) for x in sorted(unknown))
            raise ValueError(f"labels outside declared kappa levels: {bad}")
    if not resolved:
        raise ValueError("no ordinal levels to compare")
    return resolved


def _ordinal_weight(distance: int, max_distance: int, weights: str) -> float:
    if max_distance <= 0:
        return 1.0
    unit = distance / max_distance
    if weights == "linear":
        return 1.0 - unit
    if weights == "quadratic":
        return 1.0 - unit * unit
    raise ValueError(f"unknown kappa weight scheme {weights!r}; use linear or quadratic")


def weighted_cohen_kappa(
    a: dict[str, str],
    b: dict[str, str],
    *,
    weights: str = "linear",
    levels: Sequence[int] | None = None,
) -> float:
    """Weighted Cohen's kappa for ordinal integer labels (e.g. rubric scores 0-3).

    Linear weights (Cicchetti-Allison) and quadratic weights (Fleiss-Cohen)
    credit near misses more than far misses. `levels` declares the full
    ordered scale when the observed labels do not span it (typical for 0-3).
    """
    if weights not in ("linear", "quadratic"):
        raise ValueError(
            f"weighted_cohen_kappa weights must be 'linear' or 'quadratic', got {weights!r}"
        )

    shared = _shared_ids(a, b)
    n = len(shared)
    vals_a = [_parse_ordinal(a[i]) for i in shared]
    vals_b = [_parse_ordinal(b[i]) for i in shared]
    scale = _resolve_levels(vals_a, vals_b, levels)
    index = {level: idx for idx, level in enumerate(scale)}
    k = len(scale)
    max_distance = k - 1

    # Confusion counts on the declared ordinal scale.
    matrix = [[0 for _ in range(k)] for _ in range(k)]
    for va, vb in zip(vals_a, vals_b, strict=True):
        matrix[index[va]][index[vb]] += 1

    p_observed = 0.0
    for i in range(k):
        for j in range(k):
            p_observed += _ordinal_weight(abs(i - j), max_distance, weights) * (
                matrix[i][j] / n
            )

    row = [sum(matrix[i][j] for j in range(k)) / n for i in range(k)]
    col = [sum(matrix[i][j] for i in range(k)) / n for j in range(k)]
    p_expected = 0.0
    for i in range(k):
        for j in range(k):
            p_expected += (
                _ordinal_weight(abs(i - j), max_distance, weights) * row[i] * col[j]
            )

    if p_expected >= 1.0:
        return 1.0 if p_observed >= 1.0 else 0.0
    return (p_observed - p_expected) / (1.0 - p_expected)


def agreement_kappa(
    a: dict[str, str],
    b: dict[str, str],
    *,
    weights: str = "none",
    levels: Sequence[int] | None = None,
    config: KappaConfig | None = None,
) -> float:
    """Dispatch to unweighted or weighted Cohen's kappa.

    `weights="none"` keeps the binary/categorical path. `linear` / `quadratic`
    require ordinal integer labels. Prefer `config=` when calling from diagnose.
    """
    if config is not None:
        weights = config.weights
        levels = config.levels
    scheme = (weights or "none").lower()
    if scheme not in WEIGHT_SCHEMES:
        raise ValueError(
            f"kappa weights must be one of {sorted(WEIGHT_SCHEMES)}, got {weights!r}"
        )
    if scheme == "none":
        return cohen_kappa(a, b)
    return weighted_cohen_kappa(a, b, weights=scheme, levels=levels)


def flip_rate(a: dict[str, str], b: dict[str, str]) -> float:
    """Fraction of shared items whose label differs between the two labelings."""
    return 1.0 - observed_agreement(a, b)
