# Journal — judge-drift-sentinel

Append-only log of backlog ticks. One entry per day the loop advances.

## 2026-08-03 — W1 baseline command

Shipped `drift-sentinel baseline`: scores a judge run against the frozen
anchor set, records `anchor_freeze_hash` + `baseline_kappa`, and writes a
pinned baseline JSON usable by `check`. Module `driftsentinel.baseline`
(`pin_baseline` / `write_baseline`). 31 tests green, ruff clean.

## 2026-08-03 — W2 freeze-hash enforcement

`drift-sentinel check` now refuses when a pinned baseline's
`anchor_freeze_hash` no longer matches the loaded anchor file
(`enforce_anchor_freeze` / `load_recorded_freeze_hash`). Legacy plain-run
baselines without the field still compare. Named test:
`test_check_refuses_when_pinned_baseline_freeze_hash_mismatches`.

## 2026-08-04 — W3 weighted kappa for ordinal rubrics

Added pure-Python weighted Cohen's kappa (`linear` / `quadratic`) for
ordinal integer labels such as 0-3 rubrics. `drift-sentinel check` and
`baseline` take `--kappa-weights` / `--kappa-levels`; default `none` keeps
the binary unweighted path. Central test:
`test_weighted_kappa_separates_near_miss_from_far_miss_on_ordinal_scale`.
43 tests green, ruff clean.

## 2026-08-04 — W4 history timeline / slow decay

Added `drift-sentinel history`: ordered N-run verdict + kappa timeline via
`driftsentinel.history.build_history`. Flags slow decay when the first→last
kappa drop exceeds `--kappa-drop` while no consecutive pair alone does —
the failure mode pairwise `check` cannot see. Central test:
`test_history_flags_slow_decay_that_pairwise_checks_miss`. Exit 2 on
JUDGE_DRIFT or slow decay. 49 tests green, ruff clean.

## 2026-08-04 — W5 weekly CI re-score / issue on JUDGE_DRIFT

Shipped `.github/workflows/weekly-anchor-rescore.yml`: Monday cron +
`workflow_dispatch`, runs `drift-sentinel check` or `history`, opens or
comments a GitHub issue via `gh` + `GITHUB_TOKEN` when exit code is 2
(`JUDGE_DRIFT`), then fails the job. Schedule defaults use the
SYSTEM_CHANGE example path to avoid weekly spam from the intentional
drift demo. README documents path inputs and secret wiring (no PATs in
repo). Named test:
`test_weekly_rescore_workflow_opens_issue_on_judge_drift`. 50 tests green,
ruff clean.

## 2026-08-04 — W6 judgekit panel-export adapter

Shipped `driftsentinel.adapter` + `drift-sentinel import-judgekit`: reads
`judgekit.panel_export/v1` (human_labels + replicated ratings) or bare
judgekit ratings with `--human-labels`, collapses one judge via modal/first
into sentinel anchors JSONL + run JSON. Example fixture
`examples/judgekit_panel_export.json`. Named test:
`test_adapter_reads_anchor_scores_straight_from_judgekit_panel_export`.
59 tests green, ruff clean.

## 2026-08-04 — W7 loop-engine gate docs

Documented wiring `drift-sentinel check` as an agent-loop-engine
`--gate NAME=COMMAND`, with exit-code table and remapper
`examples/as_loop_gate.py` so SYSTEM_CHANGE (exit 3) stays gate-green while
JUDGE_DRIFT (exit 2) trips **repair beats progress**. Snippet backlog
`examples/LOOP_STATE.md`. Named tests in `test_loop_engine_gate_docs.py`.
62 tests green, ruff clean.

## 2026-08-09 — GFI #9 drifting history fixture test

Locked `examples/drifting/` into CI via
`tests/test_history_example.py::test_examples_drifting_history_exits_2_with_judge_drift`:
same CLI path as the fixture README, asserts exit 2 and a step line with
`JUDGE_DRIFT`. 63 tests green, ruff clean.

## 2026-08-10 — evening HOLD

HOLD product scope. Gates green; refreshed NEXT TICK to evening
2026-08-10 for README `.[dev]` optional-dependencies only.
