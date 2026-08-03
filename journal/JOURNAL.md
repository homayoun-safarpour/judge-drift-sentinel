# Journal — judge-drift-sentinel

Append-only log of backlog ticks. One entry per day the loop advances.

## 2026-08-03 — W1 baseline command

Shipped `drift-sentinel baseline`: scores a judge run against the frozen
anchor set, records `anchor_freeze_hash` + `baseline_kappa`, and writes a
pinned baseline JSON usable by `check`. Module `driftsentinel.baseline`
(`pin_baseline` / `write_baseline`). 31 tests green, ruff clean.
