"""Named claim: the weekly CI example opens an issue on JUDGE_DRIFT."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "weekly-anchor-rescore.yml"


def test_weekly_rescore_workflow_opens_issue_on_judge_drift() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert WORKFLOW.is_file()
    assert "cron:" in text
    assert "workflow_dispatch" in text
    assert "drift-sentinel check" in text
    assert "drift-sentinel history" in text
    assert "JUDGE_DRIFT" in text
    assert "gh issue create" in text
    assert "GITHUB_TOKEN" in text
    assert "permissions:" in text
    assert "issues: write" in text
    # Defaults must not point the schedule at the intentional drift demo
    # (that would spam issues every Monday).
    assert "examples/run_current_system.json" in text
    assert "secrets.OPENAI" not in text.upper()
    assert "sk-" not in text
