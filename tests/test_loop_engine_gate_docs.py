"""Named claim: README + as_loop_gate wire drift-sentinel for loop-engine."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GATE = ROOT / "examples" / "as_loop_gate.py"
EXAMPLES = ROOT / "examples"


def _load_as_loop_gate():
    spec = importlib.util.spec_from_file_location("as_loop_gate", GATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_readme_documents_loop_engine_gate_exit_code_contract() -> None:
    text = README.read_text(encoding="utf-8")
    assert "agent-loop-engine" in text
    assert "--gate" in text
    assert "as_loop_gate.py" in text
    assert "repair beats progress" in text or "repair-beats-progress" in text
    # Three-way sentinel exits must stay explicit (CI / scripts that care).
    assert "STABLE" in text and "exit" in text.lower()
    assert "SYSTEM_CHANGE" in text
    assert "JUDGE_DRIFT" in text
    # Remap rule: SYSTEM_CHANGE must not falsely red the loop gate.
    assert "exit 3" in text or "exit code 3" in text or "`3`" in text


def test_as_loop_gate_remaps_system_change_to_pass_and_judge_drift_to_fail() -> None:
    """Hiring claim: only JUDGE_DRIFT (not SYSTEM_CHANGE) trips repair."""
    remap = _load_as_loop_gate().remap_for_loop_engine
    assert remap(0) == 0  # STABLE
    assert remap(3) == 0  # SYSTEM_CHANGE -> green for loop
    assert remap(2) == 2  # JUDGE_DRIFT -> red
    assert remap(1) == 1  # wiring error -> red


def test_as_loop_gate_script_exit_codes_on_shipped_examples() -> None:
    py = sys.executable
    base = [
        py,
        str(GATE),
        "--anchors",
        str(EXAMPLES / "anchors.jsonl"),
        "--baseline",
        str(EXAMPLES / "run_baseline.json"),
    ]
    system = subprocess.run(
        [*base, "--current", str(EXAMPLES / "run_current_system.json")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert system.returncode == 0, system.stdout + system.stderr
    assert "SYSTEM_CHANGE" in system.stdout

    drift = subprocess.run(
        [*base, "--current", str(EXAMPLES / "run_current.json")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert drift.returncode == 2, drift.stdout + drift.stderr
    assert "JUDGE_DRIFT" in drift.stdout
