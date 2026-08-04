"""The verdict: given two runs over one frozen anchor set, who moved?

Decision policy, in priority order:

1. JUDGE_DRIFT  - the judge's agreement with the frozen human labels fell
                  by more than `kappa_drop`. The ruler moved; do not trust
                  any live-metric movement between these runs.
2. SYSTEM_CHANGE - anchor agreement held, but the live eval metric moved by
                  more than `metric_shift`. The ruler is steady; the score
                  movement is real and belongs to your system.
3. STABLE       - neither moved beyond threshold.

An unpinned judge (fingerprint changed between runs) never changes the
verdict on its own - the anchor set is the evidence - but it is always
reported, because it is the usual cause of drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from driftsentinel.agreement import DEFAULT_KAPPA, KappaConfig, agreement_kappa, flip_rate
from driftsentinel.anchors import AnchorSet
from driftsentinel.runs import JudgeRun

JUDGE_DRIFT = "JUDGE_DRIFT"
SYSTEM_CHANGE = "SYSTEM_CHANGE"
STABLE = "STABLE"

#: Exit codes for gate composition: 0 means "your eval numbers are trustworthy".
EXIT_CODES = {STABLE: 0, SYSTEM_CHANGE: 3, JUDGE_DRIFT: 2}


@dataclass(frozen=True)
class Verdict:
    kind: str
    reason: str
    baseline_kappa: float
    current_kappa: float
    anchor_flip_rate: float
    judge_pinned: bool
    baseline_fingerprint: str
    current_fingerprint: str
    metric_delta: float | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.kind]


def _require_full_coverage(anchors: AnchorSet, run: JudgeRun) -> None:
    missing = anchors.ids() - set(run.anchor_scores)
    if missing:
        names = ", ".join(sorted(missing)[:5])
        raise ValueError(
            f"run {run.source or run.fingerprint} did not score every anchor "
            f"(missing {len(missing)}: {names}). A partial re-score is not comparable."
        )


def diagnose(  # noqa: PLR0913 — policy knobs stay keyword-only beside the three runs
    anchors: AnchorSet,
    baseline: JudgeRun,
    current: JudgeRun,
    *,
    kappa_drop: float = 0.10,
    metric_shift: float = 0.05,
    kappa: KappaConfig | None = None,
) -> Verdict:
    """Attribute score movement between two runs to the judge or to the system.

    Pass `kappa=KappaConfig(weights="linear"|"quadratic", levels=(0,1,2,3))`
    for ordinal rubrics; default is unweighted Cohen's kappa.
    """
    _require_full_coverage(anchors, baseline)
    _require_full_coverage(anchors, current)
    kappa_cfg = kappa or DEFAULT_KAPPA

    k_baseline = agreement_kappa(
        anchors.labels,
        baseline.anchor_scores,
        config=kappa_cfg,
    )
    k_current = agreement_kappa(
        anchors.labels,
        current.anchor_scores,
        config=kappa_cfg,
    )
    flips = flip_rate(baseline.anchor_scores, current.anchor_scores)
    pinned = baseline.fingerprint == current.fingerprint

    notes = []
    if not pinned:
        notes.append(
            f"judge is not pinned: {baseline.fingerprint} -> {current.fingerprint}"
        )

    metric_delta = None
    if baseline.live_metric is not None and current.live_metric is not None:
        metric_delta = current.live_metric - baseline.live_metric

    if k_baseline - k_current > kappa_drop:
        kind = JUDGE_DRIFT
        reason = (
            "agreement with the frozen human labels fell "
            f"({k_baseline:.3f} -> {k_current:.3f}); the ruler moved, not the system"
        )
        if metric_delta is not None:
            notes.append(
                f"live metric moved {metric_delta:+.3f} but is untrustworthy under judge drift"
            )
    elif metric_delta is not None and abs(metric_delta) > metric_shift:
        kind = SYSTEM_CHANGE
        reason = (
            f"anchor agreement held ({k_baseline:.3f} -> {k_current:.3f}) while the live "
            f"metric moved {metric_delta:+.3f}; the movement is real and belongs to your system"
        )
    else:
        kind = STABLE
        reason = "anchor agreement and live metric are both within thresholds"

    return Verdict(
        kind=kind,
        reason=reason,
        baseline_kappa=k_baseline,
        current_kappa=k_current,
        anchor_flip_rate=flips,
        judge_pinned=pinned,
        baseline_fingerprint=baseline.fingerprint,
        current_fingerprint=current.fingerprint,
        metric_delta=metric_delta,
        notes=tuple(notes),
    )
