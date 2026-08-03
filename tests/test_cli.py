import json
from pathlib import Path

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
