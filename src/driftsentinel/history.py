"""Verdict timeline across N pinned runs — catch slow judge decay pairwise checks miss.

A single `check` only sees two snapshots. If kappa falls 0.04 each week for four
weeks, every pairwise step stays under the default 0.10 drop and reports STABLE,
while the ruler has quietly lost 0.16. `history` walks an ordered sequence of
runs, diagnoses each consecutive pair, and flags that cumulative erosion.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from driftsentinel.agreement import DEFAULT_KAPPA, KappaConfig, agreement_kappa
from driftsentinel.anchors import AnchorSet
from driftsentinel.runs import JudgeRun
from driftsentinel.verdict import JUDGE_DRIFT, STABLE, SYSTEM_CHANGE, Verdict, diagnose

EXIT_CODES = {STABLE: 0, SYSTEM_CHANGE: 3, JUDGE_DRIFT: 2}
_MIN_RUNS = 2


@dataclass(frozen=True)
class TimelineStep:
    """One consecutive pair on the timeline."""

    index: int
    from_source: str
    to_source: str
    verdict: Verdict


@dataclass(frozen=True)
class HistoryReport:
    """Full timeline plus the slow-decay signal pairwise checks cannot see."""

    steps: tuple[TimelineStep, ...]
    first_kappa: float
    last_kappa: float
    cumulative_kappa_drop: float
    slow_decay: bool
    slow_decay_reason: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def exit_code(self) -> int:
        if self.slow_decay or any(s.verdict.kind == JUDGE_DRIFT for s in self.steps):
            return EXIT_CODES[JUDGE_DRIFT]
        if any(s.verdict.kind == SYSTEM_CHANGE for s in self.steps):
            return EXIT_CODES[SYSTEM_CHANGE]
        return EXIT_CODES[STABLE]


def build_history(  # noqa: PLR0913 — policy knobs stay keyword-only beside the runs
    anchors: AnchorSet,
    runs: Sequence[JudgeRun],
    *,
    kappa_drop: float = 0.10,
    metric_shift: float = 0.05,
    kappa: KappaConfig | None = None,
) -> HistoryReport:
    """Diagnose consecutive pairs and flag slow decay across the whole sequence.

    Slow decay fires when the first→last kappa drop exceeds `kappa_drop` but no
    consecutive pair itself crossed that threshold (so every pairwise `check`
    would have looked fine).
    """
    if len(runs) < _MIN_RUNS:
        raise ValueError("history needs at least two run files to build a timeline")

    kappa_cfg = kappa or DEFAULT_KAPPA
    steps: list[TimelineStep] = []
    for i in range(len(runs) - 1):
        left, right = runs[i], runs[i + 1]
        verdict = diagnose(
            anchors,
            left,
            right,
            kappa_drop=kappa_drop,
            metric_shift=metric_shift,
            kappa=kappa_cfg,
        )
        steps.append(
            TimelineStep(
                index=i + 1,
                from_source=left.source or f"run[{i}]",
                to_source=right.source or f"run[{i + 1}]",
                verdict=verdict,
            )
        )

    first_kappa = agreement_kappa(
        anchors.labels,
        runs[0].anchor_scores,
        config=kappa_cfg,
    )
    last_kappa = agreement_kappa(
        anchors.labels,
        runs[-1].anchor_scores,
        config=kappa_cfg,
    )
    cumulative = first_kappa - last_kappa

    pairwise_drift = any(s.verdict.kind == JUDGE_DRIFT for s in steps)
    # Slow decay: the ruler eroded across the window, but no single step
    # crossed the threshold that a lone `check` would catch.
    slow_decay = cumulative > kappa_drop and not pairwise_drift
    reason = ""
    if slow_decay:
        reason = (
            f"cumulative kappa drop {cumulative:.3f} exceeds threshold {kappa_drop:.3f} "
            f"({first_kappa:.3f} -> {last_kappa:.3f}) while no consecutive pair alone "
            "crossed it; pairwise checks would have missed this erosion"
        )

    notes: list[str] = []
    if pairwise_drift:
        notes.append("at least one consecutive pair already reports JUDGE_DRIFT")
    if any(s.verdict.kind == SYSTEM_CHANGE for s in steps):
        notes.append("at least one consecutive pair reports SYSTEM_CHANGE")

    return HistoryReport(
        steps=tuple(steps),
        first_kappa=first_kappa,
        last_kappa=last_kappa,
        cumulative_kappa_drop=cumulative,
        slow_decay=slow_decay,
        slow_decay_reason=reason,
        notes=tuple(notes),
    )
