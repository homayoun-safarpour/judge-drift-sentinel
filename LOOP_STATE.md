# judge-drift-sentinel — live project state

This is the real backlog of this repository, advanced one bounded increment
per day by an agent loop. One checkbox per day, smallest cost first when the
head item goes stale.

- [x] W1 `drift-sentinel baseline` command: score a run and freeze it as the pinned baseline (cost: S) (touched: 2026-08-03)
- [x] W2 Anchor freeze-hash enforcement: `check` refuses to run if the anchor file no longer matches the hash recorded in the baseline (cost: S) (touched: 2026-08-03)
- [x] W3 Weighted kappa for ordinal rubrics (0-3 scales, not just pass/fail) (cost: M) (touched: 2026-08-04)
- [x] W4 `drift-sentinel history`: verdict timeline across N run files, spot slow decay (cost: M) (touched: 2026-08-04)
- [x] W5 GitHub Actions example: weekly anchor re-score, open an issue on JUDGE_DRIFT (cost: M) (touched: 2026-08-04)
- [ ] W6 Adapter: read anchor scores straight from a judge-reliability-kit panel export (cost: M)
- [ ] W7 Docs: wiring `drift-sentinel check` as an agent-loop-engine gate (cost: S)
- [ ] W8 Publish to PyPI so `pip install judge-drift-sentinel` is true (cost: M)
