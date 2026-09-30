from pathlib import Path

from driftsentinel.cli import main

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
EXAMPLES = ROOT / "examples"


def test_readme_spoken_h1_is_drift_sentinel():
    assert README.lstrip().startswith("# drift-sentinel\n")
    assert "judge-drift-sentinel" in README


def test_readme_first_screen_matches_top100_craft():
    pip_at = README.find("pip install")
    interview_at = README.find("Interview pack")
    problem_at = README.find("## The problem")
    assert 0 <= pip_at < interview_at
    assert 0 <= pip_at < problem_at
    head = "\n".join(README.splitlines()[:22])
    assert "# drift-sentinel" in head
    assert "git clone https://github.com/homayoun-safarpour/judge-drift-sentinel" in head
    assert "pip install -e" in head
    assert "examples/run_current.json" in head
    assert "verdict      : JUDGE_DRIFT" in head
    assert "0.833 -> 0.333" in head
    assert "Interview pack" not in head
    assert "\u2014" not in head
    assert "STABLE" not in head


def test_readme_stranger_check_is_judge_drift():
    code = main(
        [
            "check",
            "--anchors",
            str(EXAMPLES / "anchors.jsonl"),
            "--baseline",
            str(EXAMPLES / "run_baseline.json"),
            "--current",
            str(EXAMPLES / "run_current.json"),
        ]
    )
    assert code == 2
