"""Adapter: judge-reliability-kit panel export -> AnchorSet / JudgeRun."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftsentinel.adapter import (
    SCHEMA_VERSION,
    load_panel_export,
    modal_label,
    panel_to_anchors,
    panel_to_run,
    parse_panel_dict,
    write_anchors_jsonl,
)
from driftsentinel.cli import main
from driftsentinel.runs import load_run

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
PANEL = EXAMPLES / "judgekit_panel_export.json"


def test_modal_label_majority_wins_on_tie_breaker_first_seen():
    assert modal_label(["fail", "pass", "fail"]) == "fail"
    assert modal_label(["pass", "pass", "fail", "fail"]) == "pass"


def test_load_panel_export_reads_judgekit_v1_envelope():
    panel = load_panel_export(PANEL)
    assert panel.schema_version == SCHEMA_VERSION
    assert panel.human_labels["a01"] == "pass"
    assert panel.ratings["a05"]["gpt-4o-judge"] == ["fail", "fail", "pass", "fail"]
    assert panel.judges["gpt-4o-judge"]["prompt_sha"] == "kit-demo-01"


def test_panel_to_run_uses_modal_aggregate_like_judgekit():
    panel = load_panel_export(PANEL)
    run = panel_to_run(panel, "gpt-4o-judge", aggregate="modal")
    assert run.model == "gpt-4o-judge"
    assert run.prompt_sha == "kit-demo-01"
    assert run.anchor_scores["a05"] == "fail"  # 3 fail vs 1 pass
    assert run.live_metric == pytest.approx(0.81)


def test_panel_to_run_first_aggregate_keeps_single_pass():
    panel = load_panel_export(PANEL)
    run = panel_to_run(panel, "gpt-4o-judge", aggregate="first")
    assert run.anchor_scores["a05"] == "fail"


def test_panel_to_anchors_freeze_hash_stable(tmp_path):
    panel = load_panel_export(PANEL)
    anchors = panel_to_anchors(panel)
    out = write_anchors_jsonl(tmp_path / "anchors.jsonl", anchors)
    assert anchors.freeze_hash == panel_to_anchors(load_panel_export(PANEL)).freeze_hash
    assert out.read_text(encoding="utf-8").count("\n") == len(anchors.labels)


def test_bare_ratings_need_human_labels(tmp_path):
    bare = {
        "a01": {"gpt-4o-judge": ["pass", "pass"]},
        "a02": {"gpt-4o-judge": ["fail", "fail"]},
    }
    path = tmp_path / "ratings.json"
    path.write_text(json.dumps(bare), encoding="utf-8")
    with pytest.raises(ValueError, match="human_labels"):
        load_panel_export(path)

    gold = tmp_path / "gold.json"
    gold.write_text(json.dumps({"a01": "pass", "a02": "fail"}), encoding="utf-8")
    panel = load_panel_export(path, human_labels_path=gold)
    run = panel_to_run(panel, "gpt-4o-judge")
    assert run.anchor_scores == {"a01": "pass", "a02": "fail"}


def test_missing_judge_ratings_for_labeled_item_are_rejected():
    panel = parse_panel_dict(
        {
            "schema_version": SCHEMA_VERSION,
            "human_labels": {"a01": "pass", "a02": "fail"},
            "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
        }
    )
    with pytest.raises(ValueError, match="no ratings for human-labeled"):
        panel_to_run(panel, "gpt-4o-judge")


def test_import_judgekit_cli_writes_files_usable_by_check(tmp_path, capsys):
    anchors_out = tmp_path / "anchors.jsonl"
    run_out = tmp_path / "run.json"
    code = main(
        [
            "import-judgekit",
            "--panel",
            str(PANEL),
            "--judge",
            "gpt-4o-judge",
            "--anchors-out",
            str(anchors_out),
            "--run-out",
            str(run_out),
            "--json",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["imported"] is True
    assert summary["n_anchors"] == 6
    assert summary["fingerprint"] == "gpt-4o-judge@kit-demo-01"

    run = load_run(run_out)
    assert run.anchor_scores["a01"] == "pass"

    # Round-trip: imported artifacts work as a stable self-check.
    check_code = main(
        [
            "check",
            "--anchors",
            str(anchors_out),
            "--baseline",
            str(run_out),
            "--current",
            str(run_out),
        ]
    )
    assert check_code == 0


def test_adapter_reads_anchor_scores_straight_from_judgekit_panel_export():
    """Named claim: no hand-copy — panel export alone yields JudgeRun scores."""
    panel = load_panel_export(PANEL)
    run = panel_to_run(panel, "claude-judge")
    assert set(run.anchor_scores) == set(panel.human_labels)
    assert all(isinstance(v, str) and v for v in run.anchor_scores.values())


def test_import_judgekit_cli_locks_panel_envelope_and_documented_flags(tmp_path, capsys):
    """Named claim: example panel fields and documented import-judgekit flags round-trip.

    Locks ``examples/judgekit_panel_export.json`` envelope keys (created,
    live_metric, judges fingerprints) and CLI flags documented in README /
    ``--help``: ``--human-labels`` (nested gold map), ``--aggregate``,
    ``--model``, ``--prompt-sha``.
    """
    panel = load_panel_export(PANEL)
    assert panel.schema_version == SCHEMA_VERSION
    assert panel.created == "2026-08-04"
    assert panel.live_metric == pytest.approx(0.81)
    assert set(panel.judges) == {"gpt-4o-judge", "claude-judge"}

    anchors_out = tmp_path / "anchors.jsonl"
    run_out = tmp_path / "run.json"
    code = main(
        [
            "import-judgekit",
            "--panel",
            str(PANEL),
            "--judge",
            "gpt-4o-judge",
            "--anchors-out",
            str(anchors_out),
            "--run-out",
            str(run_out),
            "--json",
        ]
    )
    assert code == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["aggregate"] == "modal"
    assert summary["schema_version"] == SCHEMA_VERSION

    written = json.loads(run_out.read_text(encoding="utf-8"))
    assert written["created"] == "2026-08-04"
    assert written["live_metric"] == pytest.approx(0.81)
    assert written["judge"] == {"model": "gpt-4o-judge", "prompt_sha": "kit-demo-01"}
    assert written["anchor_scores"]["a05"] == "fail"  # modal of fixture replicates

    override_run = tmp_path / "run_override.json"
    code = main(
        [
            "import-judgekit",
            "--panel",
            str(PANEL),
            "--judge",
            "gpt-4o-judge",
            "--aggregate",
            "first",
            "--model",
            "override-model",
            "--prompt-sha",
            "override-sha",
            "--anchors-out",
            str(tmp_path / "anchors2.jsonl"),
            "--run-out",
            str(override_run),
            "--json",
        ]
    )
    assert code == 0
    override_summary = json.loads(capsys.readouterr().out)
    assert override_summary["aggregate"] == "first"
    assert override_summary["fingerprint"] == "override-model@override-sha"
    override_payload = json.loads(override_run.read_text(encoding="utf-8"))
    assert override_payload["judge"] == {"model": "override-model", "prompt_sha": "override-sha"}
    assert override_payload["anchor_scores"]["a05"] == "fail"  # first replicate in fixture

    bare = tmp_path / "ratings.json"
    bare.write_text(
        json.dumps(
            {
                "a01": {"gpt-4o-judge": ["pass", "pass"]},
                "a02": {"gpt-4o-judge": ["fail", "fail"]},
            }
        ),
        encoding="utf-8",
    )
    nested_gold = tmp_path / "gold_nested.json"
    nested_gold.write_text(
        json.dumps({"human_labels": {"a01": "pass", "a02": "fail"}}),
        encoding="utf-8",
    )
    bare_run = tmp_path / "bare_run.json"
    code = main(
        [
            "import-judgekit",
            "--panel",
            str(bare),
            "--human-labels",
            str(nested_gold),
            "--judge",
            "gpt-4o-judge",
            "--anchors-out",
            str(tmp_path / "bare_anchors.jsonl"),
            "--run-out",
            str(bare_run),
        ]
    )
    assert code == 0
    assert load_run(bare_run).anchor_scores == {"a01": "pass", "a02": "fail"}
