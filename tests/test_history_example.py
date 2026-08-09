"""Named claim: examples/drifting history CLI exits 2 with JUDGE_DRIFT."""

from __future__ import annotations

from pathlib import Path

from driftsentinel.cli import main

DRIFTING = Path(__file__).resolve().parent.parent / "examples" / "drifting"


def test_examples_drifting_history_exits_2_with_judge_drift(capsys) -> None:
    """Lock the community drifting fixture to the README CLI path.

    Acceptance (GFI #9): exit code 2 and at least one printed step shows
    JUDGE_DRIFT. Altering the runs to stay CLEAN must fail this test.
    """
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
    out = capsys.readouterr().out
    assert code == 2
    assert "JUDGE_DRIFT" in out
    # At least one consecutive step line must report the verdict (not only
    # the footer note).
    step_lines = [line for line in out.splitlines() if line.startswith("step ")]
    assert any("JUDGE_DRIFT" in line for line in step_lines)
