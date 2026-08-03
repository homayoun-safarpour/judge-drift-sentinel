import json
from pathlib import Path

import pytest

from driftsentinel.anchors import AnchorSet, load_anchors
from driftsentinel.baseline import (
    enforce_anchor_freeze,
    load_recorded_freeze_hash,
    pin_baseline,
    write_baseline,
)
from driftsentinel.cli import main
from driftsentinel.runs import JudgeRun, load_run

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def test_pin_baseline_records_freeze_hash_and_kappa():
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    run = load_run(EXAMPLES / "run_baseline.json")
    payload = pin_baseline(anchors, run)

    assert payload["pinned"] is True
    assert payload["anchor_freeze_hash"] == anchors.freeze_hash
    assert payload["baseline_kappa"] == pytest.approx(0.833333, abs=1e-5)
    assert payload["judge"]["model"] == "frontier-4-2026-05-01"
    assert payload["anchor_scores"] == run.anchor_scores
    assert payload["live_metric"] == 0.81


def test_pin_baseline_rejects_partial_coverage():
    anchors = AnchorSet(labels={"a1": "pass", "a2": "fail"})
    run = JudgeRun(model="m", prompt_sha="p", anchor_scores={"a1": "pass"})
    with pytest.raises(ValueError, match="partial re-score cannot be pinned"):
        pin_baseline(anchors, run)


def test_write_baseline_is_loadable_by_check(tmp_path):
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    run = load_run(EXAMPLES / "run_baseline.json")
    out = tmp_path / "pinned.json"
    write_baseline(out, pin_baseline(anchors, run))

    reloaded = load_run(out)
    assert reloaded.fingerprint == run.fingerprint
    assert reloaded.anchor_scores == run.anchor_scores

    # Still usable as --baseline for check against itself -> STABLE
    code = main([
        "check",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--baseline", str(out),
        "--current", str(EXAMPLES / "run_baseline.json"),
    ])
    assert code == 0


def test_cli_baseline_writes_pinned_file(tmp_path, capsys):
    out = tmp_path / "baseline.json"
    code = main([
        "baseline",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--run", str(EXAMPLES / "run_baseline.json"),
        "--out", str(out),
    ])
    assert code == 0
    printed = capsys.readouterr().out
    assert "pinned       : yes" in printed
    assert "freeze hash  :" in printed
    assert out.exists()

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pinned"] is True
    assert "anchor_freeze_hash" in payload
    assert payload["baseline_kappa"] > 0.8


def test_cli_baseline_json_mode(tmp_path, capsys):
    out = tmp_path / "baseline.json"
    code = main([
        "baseline",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--run", str(EXAMPLES / "run_baseline.json"),
        "--out", str(out),
        "--json",
    ])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["pinned"] is True
    assert payload["wrote"] == str(out)


def test_enforce_anchor_freeze_accepts_matching_hash():
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    enforce_anchor_freeze(anchors, anchors.freeze_hash)  # does not raise


def test_enforce_anchor_freeze_skips_when_hash_absent():
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    enforce_anchor_freeze(anchors, None)  # legacy plain-run baseline


def test_enforce_anchor_freeze_rejects_mismatch():
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    with pytest.raises(ValueError, match="anchor freeze hash mismatch"):
        enforce_anchor_freeze(anchors, "deadbeef0000")


def test_check_refuses_when_pinned_baseline_freeze_hash_mismatches(tmp_path, capsys):
    """Named behavioral claim: check refuses if anchors no longer match the pin."""
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    pinned = tmp_path / "pinned.json"
    write_baseline(pinned, pin_baseline(anchors, load_run(EXAMPLES / "run_baseline.json")))
    assert load_recorded_freeze_hash(pinned) == anchors.freeze_hash

    edited = tmp_path / "anchors_edited.jsonl"
    lines = (EXAMPLES / "anchors.jsonl").read_text(encoding="utf-8").splitlines()
    # Flip one human label so the freeze hash changes.
    edited.write_text(
        "\n".join(
            '{"id": "a01", "input": "x", "label": "fail"}' if '"id": "a01"' in line else line
            for line in lines
            if line.strip()
        )
        + "\n",
        encoding="utf-8",
    )

    code = main([
        "check",
        "--anchors", str(edited),
        "--baseline", str(pinned),
        "--current", str(EXAMPLES / "run_baseline.json"),
    ])
    assert code == 1
    err = capsys.readouterr().err
    assert "anchor freeze hash mismatch" in err


def test_check_allows_matching_pinned_baseline(tmp_path):
    anchors = load_anchors(EXAMPLES / "anchors.jsonl")
    pinned = tmp_path / "pinned.json"
    write_baseline(pinned, pin_baseline(anchors, load_run(EXAMPLES / "run_baseline.json")))

    code = main([
        "check",
        "--anchors", str(EXAMPLES / "anchors.jsonl"),
        "--baseline", str(pinned),
        "--current", str(EXAMPLES / "run_baseline.json"),
    ])
    assert code == 0
