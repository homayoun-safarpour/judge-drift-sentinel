"""Named claim: weekly CI workflow matches README trigger/input/issue path."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "weekly-anchor-rescore.yml"

# README § CI documents this exact title for the JUDGE_DRIFT issue path.
JUDGE_DRIFT_ISSUE_TITLE = "JUDGE_DRIFT: weekly anchor re-score detected judge drift"


def test_weekly_rescore_workflow_opens_issue_on_judge_drift() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert WORKFLOW.is_file()

    # Triggers (README: Mondays 06:00 UTC cron + workflow_dispatch).
    assert 'cron: "0 6 * * 1"' in text
    assert "workflow_dispatch:" in text

    # Documented path/mode inputs operators set in the Actions UI.
    for input_name in (
        "anchors:",
        "baseline:",
        "current:",
        "mode:",
        "history_runs:",
    ):
        assert input_name in text

    # Both CLI modes the README table claims.
    assert "drift-sentinel check" in text
    assert "drift-sentinel history" in text

    # Schedule / Resolve-paths defaults must not spam the intentional drift demo.
    assert "examples/anchors.jsonl" in text
    assert "examples/run_baseline.json" in text
    assert "examples/run_current_system.json" in text
    assert "IN_CURRENT:-examples/run_current_system.json" in text

    # JUDGE_DRIFT issue path: create or comment, then fail the job.
    assert JUDGE_DRIFT_ISSUE_TITLE in text
    assert "gh issue create" in text
    assert "gh issue comment" in text
    assert 'in:title JUDGE_DRIFT: weekly anchor' in text
    assert "steps.sentinel.outputs.exit_code == '2'" in text
    assert "Fail the job on JUDGE_DRIFT" in text

    # Auth: built-in token + issues write; never commit provider secrets.
    assert "GITHUB_TOKEN" in text
    assert "secrets.GITHUB_TOKEN" in text
    assert "permissions:" in text
    assert "issues: write" in text
    assert "secrets.OPENAI" not in text.upper()
    assert "sk-" not in text
