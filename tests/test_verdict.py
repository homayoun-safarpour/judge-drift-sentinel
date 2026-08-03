import pytest

from driftsentinel.anchors import AnchorSet
from driftsentinel.runs import JudgeRun
from driftsentinel.verdict import JUDGE_DRIFT, STABLE, SYSTEM_CHANGE, diagnose

HUMAN = {f"a{i:02d}": "pass" for i in range(1, 7)} | {f"a{i:02d}": "fail" for i in range(7, 13)}

# Judge agrees with the humans on 11/12 anchors (kappa 0.833).
GOOD_SCORES = dict(HUMAN) | {"a07": "pass"}

# Judge agrees on only 8/12 anchors (kappa 0.333).
DRIFTED_SCORES = dict(GOOD_SCORES) | {"a02": "fail", "a09": "pass", "a11": "pass"}


def anchors() -> AnchorSet:
    return AnchorSet(labels=dict(HUMAN))


def run(scores, metric=None, model="judge-1-2026-05-01", sha="9f2c1a") -> JudgeRun:
    return JudgeRun(model=model, prompt_sha=sha, anchor_scores=dict(scores), live_metric=metric)


def test_drift_on_frozen_anchors_blames_the_judge_not_the_system():
    """The central claim: the live metric dropped 0.15 - which looks exactly
    like a system regression - but the frozen anchors moved too, so the
    sentinel must blame the judge and mark the metric untrustworthy."""
    verdict = diagnose(anchors(), run(GOOD_SCORES, 0.81), run(DRIFTED_SCORES, 0.66))
    assert verdict.kind == JUDGE_DRIFT
    assert verdict.baseline_kappa == pytest.approx(5 / 6)
    assert verdict.current_kappa == pytest.approx(1 / 3)
    assert any("untrustworthy" in note for note in verdict.notes)


def test_stable_anchors_with_moving_metric_blames_the_system():
    verdict = diagnose(anchors(), run(GOOD_SCORES, 0.81), run(GOOD_SCORES, 0.66))
    assert verdict.kind == SYSTEM_CHANGE
    assert verdict.metric_delta == pytest.approx(-0.15)


def test_nothing_moving_is_stable():
    verdict = diagnose(anchors(), run(GOOD_SCORES, 0.81), run(GOOD_SCORES, 0.80))
    assert verdict.kind == STABLE


def test_judge_drift_wins_over_system_change_when_both_fire():
    # Priority matters: a drifted judge invalidates the metric comparison,
    # so JUDGE_DRIFT must win even though the metric also moved.
    verdict = diagnose(anchors(), run(GOOD_SCORES, 0.90), run(DRIFTED_SCORES, 0.50))
    assert verdict.kind == JUDGE_DRIFT


def test_missing_live_metric_still_detects_judge_drift():
    verdict = diagnose(anchors(), run(GOOD_SCORES), run(DRIFTED_SCORES))
    assert verdict.kind == JUDGE_DRIFT
    assert verdict.metric_delta is None


def test_unpinned_judge_is_reported_but_not_convicted_without_anchor_evidence():
    baseline = run(GOOD_SCORES, 0.81)
    current = run(GOOD_SCORES, 0.80, model="judge-1-latest")
    verdict = diagnose(anchors(), baseline, current)
    assert verdict.kind == STABLE
    assert not verdict.judge_pinned
    assert any("not pinned" in note for note in verdict.notes)


def test_partial_anchor_coverage_is_rejected():
    partial = dict(GOOD_SCORES)
    del partial["a05"]
    with pytest.raises(ValueError, match="did not score every anchor"):
        diagnose(anchors(), run(GOOD_SCORES), run(partial))


def test_thresholds_are_configurable():
    verdict = diagnose(
        anchors(),
        run(GOOD_SCORES, 0.81),
        run(DRIFTED_SCORES, 0.66),
        kappa_drop=0.60,
        metric_shift=0.20,
    )
    assert verdict.kind == STABLE
