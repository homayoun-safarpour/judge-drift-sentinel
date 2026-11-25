"""Inputs that cannot give a trustworthy verdict must exit 1, never STABLE."""

import json
import math

import pytest

from driftsentinel.anchors import AnchorSet, load_anchors
from driftsentinel.baseline import pin_baseline
from driftsentinel.cli import main
from driftsentinel.history import build_history
from driftsentinel.runs import JudgeRun, load_run
from driftsentinel.verdict import diagnose

IDS = [f"a{i:02d}" for i in range(1, 11)]
BALANCED = {i: ("pass" if k < 5 else "fail") for k, i in enumerate(IDS)}
FLIPPED = {i: ("fail" if lab == "pass" else "pass") for i, lab in BALANCED.items()}


def write_anchors(path, labels, inputs=None):
    lines = []
    for anchor_id, label in labels.items():
        record = {"id": anchor_id, "input": (inputs or {}).get(anchor_id, "q"), "label": label}
        lines.append(json.dumps(record))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_run(path, scores, metric=0.8):
    record = {"judge": {"model": "m1", "prompt_sha": "s"}, "anchor_scores": scores}
    if metric is not None:
        record["live_metric"] = metric
    path.write_text(json.dumps(record), encoding="utf-8")
    return path


def check(tmp_path, anchors, baseline, current, *extra):
    return main([
        "check",
        "--anchors", str(write_anchors(tmp_path / "anchors.jsonl", anchors)),
        "--baseline", str(write_run(tmp_path / "base.json", **baseline)),
        "--current", str(write_run(tmp_path / "cur.json", **current)),
        *extra,
    ])


# 1. Single-label anchor sets: kappa is undefined, so the tool refuses.

def test_single_label_anchor_set_is_refused_not_stable(tmp_path, capsys):
    single = {i: "pass" for i in IDS}
    base = {i: ("pass" if k < 9 else "fail") for k, i in enumerate(IDS)}
    cur = {i: ("pass" if k < 1 else "fail") for k, i in enumerate(IDS)}
    code = check(tmp_path, single, {"scores": base}, {"scores": cur})
    captured = capsys.readouterr()
    assert code == 1
    assert "STABLE" not in captured.out
    assert "only one human label" in captured.err
    assert "Traceback" not in captured.err


def test_single_label_anchor_set_is_refused_by_diagnose_baseline_and_history():
    anchors = AnchorSet(labels={i: "pass" for i in IDS})
    run = JudgeRun(model="m1", prompt_sha="s", anchor_scores={i: "pass" for i in IDS})
    with pytest.raises(ValueError, match="only one human label"):
        diagnose(anchors, run, run)
    with pytest.raises(ValueError, match="only one human label"):
        pin_baseline(anchors, run)
    with pytest.raises(ValueError, match="only one human label"):
        build_history(anchors, [run, run])


# 2. Thresholds that cannot fire are refused.

@pytest.mark.parametrize("value", ["nan", "inf", "5", "2", "0", "-0.1"])
def test_kappa_drop_that_disables_the_check_is_refused(tmp_path, capsys, value):
    code = check(
        tmp_path, BALANCED, {"scores": BALANCED}, {"scores": FLIPPED}, "--kappa-drop", value
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "STABLE" not in captured.out
    assert "--kappa-drop" in captured.err


@pytest.mark.parametrize("value", ["nan", "inf", "-0.05"])
def test_metric_shift_that_is_not_finite_or_negative_is_refused(tmp_path, capsys, value):
    code = check(
        tmp_path, BALANCED, {"scores": BALANCED}, {"scores": BALANCED}, "--metric-shift", value
    )
    assert code == 1
    assert "--metric-shift" in capsys.readouterr().err


def test_history_refuses_nan_kappa_drop(tmp_path, capsys):
    anchors = write_anchors(tmp_path / "anchors.jsonl", BALANCED)
    r1 = write_run(tmp_path / "r1.json", BALANCED)
    r2 = write_run(tmp_path / "r2.json", FLIPPED)
    code = main([
        "history", "--anchors", str(anchors), "--runs", str(r1), str(r2), "--kappa-drop", "nan",
    ])
    assert code == 1
    assert "--kappa-drop" in capsys.readouterr().err


# 3. A live metric that cannot be compared is refused.

def test_live_metric_in_only_one_run_is_refused_not_stable(tmp_path, capsys):
    code = check(
        tmp_path, BALANCED, {"scores": BALANCED}, {"scores": BALANCED, "metric": None}
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "STABLE" not in captured.out
    assert "live_metric" in captured.err


def test_nan_live_metric_is_refused_on_load(tmp_path, capsys):
    path = tmp_path / "nan.json"
    path.write_text(
        '{"judge": {"model": "m1"}, "anchor_scores": {"a01": "pass"}, "live_metric": NaN}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="live_metric"):
        load_run(path)
    code = check(
        tmp_path, BALANCED, {"scores": BALANCED}, {"scores": BALANCED, "metric": math.nan}
    )
    assert code == 1
    assert "live_metric" in capsys.readouterr().err


def test_no_live_metric_in_either_run_is_named_in_the_output(tmp_path, capsys):
    code = check(
        tmp_path,
        BALANCED,
        {"scores": BALANCED, "metric": None},
        {"scores": BALANCED, "metric": None},
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "STABLE" in out
    assert "no live_metric in either run" in out


# 4. Bad arguments exit 1, not 2 (2 means JUDGE_DRIFT).

def test_missing_required_argument_exits_1_not_judge_drift_code(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["check", "--anchors", "a.jsonl", "--baseline", "b.json"])
    assert excinfo.value.code == 1
    assert "--current" in capsys.readouterr().err


def test_help_still_exits_0():
    with pytest.raises(SystemExit) as excinfo:
        main(["check", "--help"])
    assert excinfo.value.code == 0


# 5. The freeze hash covers the anchor inputs.

def test_freeze_hash_changes_when_an_anchor_input_is_replaced(tmp_path):
    one = load_anchors(write_anchors(tmp_path / "one.jsonl", {"a1": "pass"}, {"a1": "Is 2+2=4?"}))
    two = load_anchors(
        write_anchors(tmp_path / "two.jsonl", {"a1": "pass"}, {"a1": "totally different question"})
    )
    assert one.freeze_hash != two.freeze_hash


def test_plain_run_baseline_without_freeze_hash_is_not_checked(tmp_path, capsys):
    """Limit by design: a plain run used as --baseline carries no freeze hash,
    so check cannot tell that the anchor inputs changed since it was scored."""
    write_anchors(tmp_path / "anchors.jsonl", BALANCED, {"a01": "a different case"})
    code = main([
        "check",
        "--anchors", str(tmp_path / "anchors.jsonl"),
        "--baseline", str(write_run(tmp_path / "base.json", BALANCED)),
        "--current", str(write_run(tmp_path / "cur.json", BALANCED)),
    ])
    assert code == 0
    assert "STABLE" in capsys.readouterr().out


# 6. Malformed run JSON gives an error line, not a traceback.

@pytest.mark.parametrize(
    "payload",
    [
        "[]",
        '{"judge": "m1", "anchor_scores": {"a01": "pass"}}',
        '{"judge": {"model": "m1"}, "anchor_scores": ["a01"]}',
    ],
)
def test_malformed_run_json_gives_error_line_not_traceback(tmp_path, capsys, payload):
    anchors = write_anchors(tmp_path / "anchors.jsonl", BALANCED)
    base = write_run(tmp_path / "base.json", BALANCED)
    bad = tmp_path / "bad.json"
    bad.write_text(payload, encoding="utf-8")
    for baseline, current in ((base, bad), (bad, base)):
        code = main([
            "check", "--anchors", str(anchors),
            "--baseline", str(baseline), "--current", str(current),
        ])
        err = capsys.readouterr().err
        assert code == 1
        assert err.startswith("error:")
        assert "Traceback" not in err
