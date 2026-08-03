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
