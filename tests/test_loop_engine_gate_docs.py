"""Named claim: README + as_loop_gate wire drift-sentinel for loop-engine."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
GATE = ROOT / "examples" / "as_loop_gate.py"
SNIPPET = ROOT / "examples" / "LOOP_STATE.md"
EXAMPLES = ROOT / "examples"

# README § Gate for agent-loop-engine documents this exact tick wiring.
DOCUMENTED_TICK_STATE = "--state examples/LOOP_STATE.md"
DOCUMENTED_DRIFT_GATE = (
    'python examples/as_loop_gate.py --anchors examples/anchors.jsonl '
    "--baseline examples/run_baseline.json "
    "--current examples/run_current_system.json"
)


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

    # Documented remapper table (wrapper exits the loop actually sees).
    assert "`0` STABLE" in text and "gate green" in text
    assert "`3` SYSTEM_CHANGE" in text
    assert "`2` JUDGE_DRIFT" in text
    assert "`1` error" in text
    assert "action: repair" in text

    # Copy-paste tick: state path + drift gate command with fixture paths.
    assert DOCUMENTED_TICK_STATE in text
    assert DOCUMENTED_DRIFT_GATE in text
    assert '--gate "tests=python -m pytest -q"' in text
    # Prefer the remapper over raw check so exit 3 stays green.
    assert 'raw `--gate "drift=drift-sentinel check' in text
    assert "would mark" in text and "SYSTEM_CHANGE" in text


def test_examples_loop_state_snippet_matches_readme_gate_wiring() -> None:
    """Snippet backlog must stay aligned with the README tick command."""
    assert SNIPPET.is_file()
    text = SNIPPET.read_text(encoding="utf-8")
    assert "agent-loop-engine" in text
    assert "repair beats progress" in text or "repair-beats-progress" in text
    assert DOCUMENTED_TICK_STATE in text
    assert DOCUMENTED_DRIFT_GATE in text
    assert "SYSTEM_CHANGE" in text and "JUDGE_DRIFT" in text
    assert "as_loop_gate.py" in text
    assert "Gate for agent-loop-engine" in text


def test_as_loop_gate_remaps_system_change_to_pass_and_judge_drift_to_fail() -> None:
    """Hiring claim: only JUDGE_DRIFT (not SYSTEM_CHANGE) trips repair."""
    mod = _load_as_loop_gate()
    remap = mod.remap_for_loop_engine
    assert remap(0) == 0  # STABLE
    assert remap(3) == 0  # SYSTEM_CHANGE -> green for loop
    assert remap(2) == 2  # JUDGE_DRIFT -> red
    assert remap(1) == 1  # wiring error -> red
    # Docstring table must stay the public contract for the remapper.
    doc = mod.__doc__ or ""
    assert "STABLE" in doc and "SYSTEM_CHANGE" in doc and "JUDGE_DRIFT" in doc
    assert "0" in doc and "3" in doc and "2" in doc
    assert frozenset({0, 3}) == mod._TRUSTWORTHY


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

    stable = subprocess.run(
        [*base, "--current", str(EXAMPLES / "run_baseline.json")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert stable.returncode == 0, stable.stdout + stable.stderr
    assert "STABLE" in stable.stdout

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
