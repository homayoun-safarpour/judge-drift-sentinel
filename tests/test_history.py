"""History timeline: consecutive verdicts + slow decay pairwise checks miss."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftsentinel.anchors import AnchorSet
from driftsentinel.cli import main
from driftsentinel.history import build_history
from driftsentinel.runs import JudgeRun
from driftsentinel.verdict import JUDGE_DRIFT, STABLE, SYSTEM_CHANGE, diagnose

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"

# 40 balanced anchors so each single flip drops kappa by 0.05 (under the
# default 0.10 threshold) — room for multi-step slow decay without floating
# point edging a pairwise step over the line.
HUMAN_40 = {f"a{i:02d}": ("pass" if i <= 20 else "fail") for i in range(1, 41)}


def _run(scores: dict[str, str], metric: float | None = 0.80, *, source: str = "") -> JudgeRun:
    return JudgeRun(
        model="judge-1",
        prompt_sha="abc",
        anchor_scores=dict(scores),
        live_metric=metric,
        source=source,
    )


def _flip_pass_to_fail(base: dict[str, str], n: int) -> dict[str, str]:
    """Flip the first n pass-labeled anchors to fail (a01, a02, ...)."""
    out = dict(base)
    for i in range(1, n + 1):
        out[f"a{i:02d}"] = "fail"
    return out


def test_history_flags_slow_decay_that_pairwise_checks_miss():
    """The central claim: kappa falls 0.05 per step for four steps — each
    pairwise `check` stays under `--kappa-drop 0.10` and reports STABLE, but
    the window drop is 0.20 and history must flag slow decay (exit 2)."""
    anchors = AnchorSet(labels=dict(HUMAN_40))
    # kappa: 1.0 -> 0.95 -> 0.90 -> 0.85 -> 0.80
    runs = [
        _run(HUMAN_40, source="week1.json"),
        _run(_flip_pass_to_fail(HUMAN_40, 1), source="week2.json"),
        _run(_flip_pass_to_fail(HUMAN_40, 2), source="week3.json"),
        _run(_flip_pass_to_fail(HUMAN_40, 3), source="week4.json"),
        _run(_flip_pass_to_fail(HUMAN_40, 4), source="week5.json"),
    ]

    for left, right in zip(runs[:-1], runs[1:], strict=True):
        assert diagnose(anchors, left, right).kind == STABLE

    report = build_history(anchors, runs, kappa_drop=0.10)
    assert all(step.verdict.kind == STABLE for step in report.steps)
    assert report.first_kappa == pytest.approx(1.0)
    assert report.last_kappa == pytest.approx(0.8)
    assert report.cumulative_kappa_drop == pytest.approx(0.2)
    assert report.slow_decay is True
    assert "pairwise checks would have missed" in report.slow_decay_reason
    assert report.exit_code == 2


def test_history_timeline_reports_consecutive_verdicts():
    anchors = AnchorSet(labels=dict(HUMAN_40))
    good = dict(HUMAN_40)
    drifted = _flip_pass_to_fail(HUMAN_40, 10)  # kappa 0.5; drop 0.5 from perfect
    stable_metric = _run(good, 0.80, source="t0.json")
    system = _run(good, 0.60, source="t1.json")  # SYSTEM_CHANGE
    drift = _run(drifted, 0.60, source="t2.json")  # JUDGE_DRIFT vs t1

    report = build_history(anchors, [stable_metric, system, drift])
    assert len(report.steps) == 2
    assert report.steps[0].verdict.kind == SYSTEM_CHANGE
    assert report.steps[1].verdict.kind == JUDGE_DRIFT
    assert report.slow_decay is False  # pairwise already caught JUDGE_DRIFT
    assert report.exit_code == 2


def test_history_rejects_fewer_than_two_runs():
    anchors = AnchorSet(labels=dict(HUMAN_40))
    with pytest.raises(ValueError, match="at least two"):
        build_history(anchors, [_run(HUMAN_40)])


def test_cli_history_prints_timeline_and_flags_slow_decay(tmp_path, capsys):
    anchors_path = tmp_path / "anchors.jsonl"
    anchors_path.write_text(
        "\n".join(json.dumps({"id": k, "label": v}) for k, v in HUMAN_40.items()) + "\n",
        encoding="utf-8",
    )
    names = ["w1.json", "w2.json", "w3.json", "w4.json", "w5.json"]
    paths = []
    for n, name in enumerate(names):
        path = tmp_path / name
        path.write_text(
            json.dumps(
                {
                    "judge": {"model": "judge-1", "prompt_sha": "abc"},
                    "live_metric": 0.80,
                    "anchor_scores": _flip_pass_to_fail(HUMAN_40, n),
                }
            ),
            encoding="utf-8",
        )
        paths.append(path)

    code = main([
        "history",
        "--anchors", str(anchors_path),
        "--runs", *[str(p) for p in paths],
    ])
    assert code == 2
    out = capsys.readouterr().out
    assert "STABLE" in out
    assert "slow decay   : YES" in out
    assert "window kappa" in out


def test_cli_history_json_is_machine_readable(tmp_path, capsys):
    anchors_path = tmp_path / "anchors.jsonl"
    anchors_path.write_text(
        "\n".join(json.dumps({"id": k, "label": v}) for k, v in HUMAN_40.items()) + "\n",
        encoding="utf-8",
    )
    paths = []
    for n in range(5):
        path = tmp_path / f"r{n}.json"
        path.write_text(
            json.dumps(
                {
                    "judge": {"model": "judge-1", "prompt_sha": "abc"},
                    "anchor_scores": _flip_pass_to_fail(HUMAN_40, n),
                }
            ),
            encoding="utf-8",
        )
        paths.append(path)

    code = main([
        "history",
        "--anchors", str(anchors_path),
        "--runs", *[str(p) for p in paths],
        "--json",
    ])
    assert code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["slow_decay"] is True
    assert payload["exit_code"] == 2
    assert len(payload["steps"]) == 4
    assert payload["cumulative_kappa_drop"] == pytest.approx(0.2)


def test_cli_history_on_examples_shows_judge_drift(capsys):
    code = main([
        "history",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--runs",
        str(EXAMPLES / "run_baseline.json"),
        str(EXAMPLES / "run_current.json"),
    ])
    assert code == 2
    assert "JUDGE_DRIFT" in capsys.readouterr().out
