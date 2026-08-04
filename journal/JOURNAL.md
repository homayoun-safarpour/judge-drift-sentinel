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
