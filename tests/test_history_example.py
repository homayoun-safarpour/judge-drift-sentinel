"""Lock the community examples/drifting history path into CI.

Mirrors the CLI invocation in examples/drifting/README.md so a silent
regression that leaves those runs CLEAN cannot land without failing this test.
"""

from __future__ import annotations

from pathlib import Path

from driftsentinel.cli import main

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
DRIFTING = EXAMPLES / "drifting"


def test_examples_drifting_history_exits_2_with_judge_drift(capsys):
    code = main(
        [
            "history",
            "--anchors",
            str(DRIFTING / "anchors.jsonl"),
            "--runs",
            str(DRIFTING / "run_1.json"),
            str(DRIFTING / "run_2.json"),
            str(DRIFTING / "run_3.json"),
        ]
    )
    assert code == 2
    out = capsys.readouterr().out
    assert "JUDGE_DRIFT" in out
