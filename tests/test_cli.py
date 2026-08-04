import json
from pathlib import Path

import pytest

from driftsentinel.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def check_args(current="run_current.json", *extra):
    return [
        "check",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--baseline", str(EXAMPLES / "run_baseline.json"),
        "--current", str(EXAMPLES / current),
        *extra,
    ]


def test_cli_exit_code_2_on_judge_drift(capsys):
    assert main(check_args()) == 2
    out = capsys.readouterr().out
    assert "JUDGE_DRIFT" in out
    assert "ruler moved" in out


def test_cli_exit_code_3_on_system_change(capsys):
    assert main(check_args("run_current_system.json")) == 3
    assert "SYSTEM_CHANGE" in capsys.readouterr().out


def test_cli_exit_code_0_when_stable(capsys):
    code = main(check_args("run_baseline.json"))
    assert code == 0
    assert "STABLE" in capsys.readouterr().out


def test_cli_json_output_is_machine_readable(capsys):
    main(check_args("run_current.json", "--json"))
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "JUDGE_DRIFT"
    assert payload["exit_code"] == 2
    assert payload["judge_pinned"] is False


def test_cli_bad_input_exits_1(capsys, tmp_path):
    missing = str(tmp_path / "nope.jsonl")
    code = main([
        "check",
        "--anchors", missing,
        "--baseline", str(EXAMPLES / "run_baseline.json"),
        "--current", str(EXAMPLES / "run_current.json"),
    ])
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_cli_check_accepts_weighted_kappa_for_ordinal_labels(tmp_path, capsys):
    anchors = tmp_path / "anchors.jsonl"
    anchors.write_text(
        "\n".join(
            [
                '{"id": "a", "label": "0"}',
                '{"id": "b", "label": "1"}',
                '{"id": "c", "label": "2"}',
                '{"id": "d", "label": "3"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    baseline = {
        "judge": {"model": "judge-1", "prompt_sha": "abc"},
        "live_metric": 0.80,
        "anchor_scores": {"a": "0", "b": "1", "c": "2", "d": "3"},
    }
    current = {
        "judge": {"model": "judge-1", "prompt_sha": "abc"},
        "live_metric": 0.80,
        "anchor_scores": {"a": "0", "b": "2", "c": "2", "d": "3"},
    }
    base_path = tmp_path / "baseline.json"
    curr_path = tmp_path / "current.json"
    base_path.write_text(json.dumps(baseline), encoding="utf-8")
    curr_path.write_text(json.dumps(current), encoding="utf-8")

    code = main([
        "check",
        "--anchors", str(anchors),
        "--baseline", str(base_path),
        "--current", str(curr_path),
        "--kappa-weights", "linear",
        "--kappa-levels", "0,1,2,3",
        "--kappa-drop", "0.25",
        "--json",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["verdict"] == "STABLE"
    assert payload["baseline_kappa"] == pytest.approx(1.0)
    assert payload["current_kappa"] == pytest.approx(0.8)
