"""Adapter: judge-reliability-kit panel export -> AnchorSet / JudgeRun."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from driftsentinel.adapter import (
    SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
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


def test_unsupported_panel_schema_version_is_rejected():
    """Named claim: only judgekit.panel_export/v1 envelopes are accepted.

    A second producer format is not shipped yet. Unknown schema_version
    values fail closed; omit schema_version on a v1-shaped envelope, or use
    bare ratings + human_labels.
    """
    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS
    with pytest.raises(ValueError, match="unsupported panel schema_version"):
        parse_panel_dict(
            {
                "schema_version": "judgekit.panel_export/v2",
                "human_labels": {"a01": "pass"},
                "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
            }
        )
    # v1-shaped envelope without schema_version still parses as v1.
    panel = parse_panel_dict(
        {
            "human_labels": {"a01": "pass"},
            "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
        }
    )
    assert panel.schema_version == SCHEMA_VERSION


def test_unsupported_schema_error_locks_v1_only_escape_hatch():
    """Named claim: unsupported-schema ValueError matches the help escape hatch.

    Locks the parse-time error string so operators see the same v1-only /
    bare-ratings contract as ``import-judgekit --help``
    (``test_import_judgekit_help_locks_v1_only_schema_gate``): only
    ``judgekit.panel_export/v1`` is supported; escape by omitting
    schema_version on a v1-shaped envelope, or bare ratings + human_labels.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_panel_dict(
            {
                "schema_version": "judgekit.panel_export/v2",
                "human_labels": {"a01": "pass"},
                "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
            }
        )
    err = " ".join(str(excinfo.value).split())

    assert "unsupported panel schema_version" in err
    assert SCHEMA_VERSION in err
    assert f"only {SCHEMA_VERSION} is supported" in err
    assert "omit schema_version" in err
    assert "bare ratings" in err
    assert "human_labels" in err
    # Rejected value may appear in the message; must not list it as supported.
    supported_clause = err.split(";", 1)[-1]
    assert "panel_export/v2" not in supported_clause
    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


def test_unrecognized_panel_error_locks_v1_only_escape_hatch():
    """Named claim: unrecognized-panel ValueError matches the v1-only contract.

    Malformed panel JSON takes a different raise path than unknown
    schema_version. Locks that message to the same v1-only / bare-ratings
    escape hatch as ``test_unsupported_schema_error_locks_v1_only_escape_hatch``
    and ``test_import_judgekit_help_locks_v1_only_schema_gate`` so a wording
    drift cannot reopen a false second-format promise on this path.
    """
    with pytest.raises(ValueError) as excinfo:
        parse_panel_dict({"not_a_panel": True, "items": []})
    err = " ".join(str(excinfo.value).split())

    assert "unrecognized panel JSON" in err
    assert SCHEMA_VERSION in err
    assert f"only {SCHEMA_VERSION} is supported" in err
    assert "bare ratings" in err
    assert "human_labels" in err
    # Must not advertise a second envelope version on this path either.
    assert "panel_export/v2" not in err
    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


def test_schema_and_unrecognized_errors_share_escape_hatch_phrases():
    """Named claim: both raise paths share the operator-facing phrase set.

    Each path is claim-locked alone. This regression asserts the shared
    phrases (``only {SCHEMA_VERSION} is supported``, ``bare ratings``,
    ``human_labels``) appear in both ValueError strings so editing one
    message cannot silently split the v1-only / bare-ratings contract.
    """
    with pytest.raises(ValueError) as unsupported:
        parse_panel_dict(
            {
                "schema_version": "judgekit.panel_export/v2",
                "human_labels": {"a01": "pass"},
                "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
            }
        )
    with pytest.raises(ValueError) as unrecognized:
        parse_panel_dict({"not_a_panel": True, "items": []})

    unsupported_err = " ".join(str(unsupported.value).split())
    unrecognized_err = " ".join(str(unrecognized.value).split())
    shared = (
        f"only {SCHEMA_VERSION} is supported",
        "bare ratings",
        "human_labels",
    )
    for phrase in shared:
        assert phrase in unsupported_err
        assert phrase in unrecognized_err
    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


def test_help_and_raise_paths_share_escape_hatch_phrases(capsys):
    """Named claim: help and both raise paths share the escape-hatch phrase set.

    Raise paths are cross-locked alone
    (``test_schema_and_unrecognized_errors_share_escape_hatch_phrases``).
    Help is claim-locked alone
    (``test_import_judgekit_help_locks_v1_only_schema_gate``). This
    regression asserts the shared operator-facing contract cannot drift
    between help and either raise path: SCHEMA_VERSION / v1 citation,
    ``bare ratings``, and human-labels / ``--human-labels``.
    """
    with pytest.raises(SystemExit) as help_exc:
        main(["import-judgekit", "--help"])
    assert help_exc.value.code == 0
    help_flat = " ".join(capsys.readouterr().out.split())

    with pytest.raises(ValueError) as unsupported:
        parse_panel_dict(
            {
                "schema_version": "judgekit.panel_export/v2",
                "human_labels": {"a01": "pass"},
                "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
            }
        )
    with pytest.raises(ValueError) as unrecognized:
        parse_panel_dict({"not_a_panel": True, "items": []})

    unsupported_err = " ".join(str(unsupported.value).split())
    unrecognized_err = " ".join(str(unrecognized.value).split())

    # v1 citation on help; only-supported clause on both raise paths.
    assert SCHEMA_VERSION in help_flat
    for err in (unsupported_err, unrecognized_err):
        assert SCHEMA_VERSION in err
        assert f"only {SCHEMA_VERSION} is supported" in err

    # bare ratings on all three operator surfaces.
    for text in (help_flat, unsupported_err, unrecognized_err):
        assert "bare ratings" in text

    # human-labels: CLI flag in help; field name in raise paths.
    assert "--human-labels" in help_flat
    for err in (unsupported_err, unrecognized_err):
        assert "human_labels" in err

    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


def test_import_judgekit_cli_stderr_shares_escape_hatch_phrases(tmp_path, capsys):
    """Named claim: CLI stderr surfaces shared escape-hatch phrases and exits 1.

    Help and both library raise paths are three-way locked
    (``test_help_and_raise_paths_share_escape_hatch_phrases``). This claim
    locks the ``import-judgekit`` CLI error path: unsupported-schema and
    unrecognized panel files print the shared phrases
    (``only {SCHEMA_VERSION} is supported``, ``bare ratings``,
    ``human_labels``) on stderr and exit 1, so CLI wrapping cannot diverge
    from the library messages.
    """
    shared = (
        f"only {SCHEMA_VERSION} is supported",
        "bare ratings",
        "human_labels",
    )
    cases = (
        {
            "schema_version": "judgekit.panel_export/v2",
            "human_labels": {"a01": "pass"},
            "ratings": {"a01": {"gpt-4o-judge": ["pass", "pass"]}},
        },
        {"not_a_panel": True, "items": []},
    )
    for i, payload in enumerate(cases):
        panel_path = tmp_path / f"bad_panel_{i}.json"
        panel_path.write_text(json.dumps(payload), encoding="utf-8")
        code = main(
            [
                "import-judgekit",
                "--panel",
                str(panel_path),
                "--judge",
                "gpt-4o-judge",
                "--anchors-out",
                str(tmp_path / f"anchors_{i}.jsonl"),
                "--run-out",
                str(tmp_path / f"run_{i}.json"),
            ]
        )
        captured = capsys.readouterr()
        err_flat = " ".join(captured.err.split())
        assert code == 1
        assert "error:" in err_flat
        for phrase in shared:
            assert phrase in err_flat
        assert captured.out == ""

    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


def test_import_judgekit_help_locks_v1_only_schema_gate(capsys):
    """Named claim: import-judgekit --help states the v1-only schema gate.

    Locks CLI help so operators see the same contract as
    ``test_unsupported_panel_schema_version_is_rejected``: enveloped panels
    accept only ``judgekit.panel_export/v1`` (unknown schema_version rejected);
    bare ratings remain allowed when ``--human-labels`` supplies gold.
    """
    with pytest.raises(SystemExit) as excinfo:
        main(["import-judgekit", "--help"])
    assert excinfo.value.code == 0
    help_text = capsys.readouterr().out
    # argparse wraps long --panel help; collapse whitespace for phrase locks.
    help_flat = " ".join(help_text.split())

    assert SCHEMA_VERSION in help_flat
    assert "unknown schema_version" in help_flat
    assert "rejected" in help_flat
    assert "bare ratings" in help_flat
    assert "--human-labels" in help_flat
    # --panel help must not advertise a second envelope version.
    assert "panel_export/v2" not in help_flat
    assert frozenset({SCHEMA_VERSION}) == SUPPORTED_SCHEMA_VERSIONS


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
