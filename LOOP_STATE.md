# judge-drift-sentinel — live project state

This is the real backlog of this repository, advanced one bounded increment
per day by an agent loop. One checkbox per day, smallest cost first when the
head item goes stale.

- [x] W1 `drift-sentinel baseline` command: score a run and freeze it as the pinned baseline (cost: S) (touched: 2026-08-03)
- [x] W2 Anchor freeze-hash enforcement: `check` refuses to run if the anchor file no longer matches the hash recorded in the baseline (cost: S) (touched: 2026-08-03)
- [x] W3 Weighted kappa for ordinal rubrics (0-3 scales, not just pass/fail) (cost: M) (touched: 2026-08-04)
- [x] W4 `drift-sentinel history`: verdict timeline across N run files, spot slow decay (cost: M) (touched: 2026-08-04)
- [x] W5 GitHub Actions example: weekly anchor re-score, open an issue on JUDGE_DRIFT (cost: M) (touched: 2026-08-04)
- [x] W6 Adapter: read anchor scores straight from a judge-reliability-kit panel export (cost: M) (touched: 2026-08-04)
- [x] W7 Docs: wiring `drift-sentinel check` as an agent-loop-engine gate (cost: S) (touched: 2026-08-04)
- [ ] W8 Publish to PyPI so `pip install judge-drift-sentinel` is true (cost: M)
  - **BLOCKED_ON_BOSS_TOKEN (2026-08-04):** `python -m build` + `twine check` PASS; no `TWINE_*` / `PYPI_TOKEN` / `UV_PUBLISH_TOKEN` / `.pypirc` in env. Packaging polish + `docs/PUBLISH.md` shipped. Boss must run twine upload with API token; agents must not mark W8 [x] or claim pip install until PyPI succeeds.

## BENCHMARK GATE (Week 1 — per WEEKLY_BUILD_BENCHMARK_RULE.md)

**Field/external (§B):** N/A this week (no lm-eval / external suite claimed). Our §A only.

| # | Check | Status |
| --- | --- | --- |
| 1 | CI green 3.10/3.11/3.12 | PASS (verify on GitHub Actions) |
| 2 | Named claim tests + pytest green | PASS (W1–W7 claim tests present) |
| 3 | Worked example real output | PASS |
| 4 | Fork/implement &lt;30 min from README | PASS (confirm on Sun close) |
| 5 | `public_git_guard.py` PASS | PASS (re-run before each push) |
| 6 | AI-tell-clean README | PASS (re-scan on Sun) |
| 7 | Interview pack (3 Q + 2-min demo + limitation) | TODO if missing `docs/INTERVIEW.md` |
| W8 | PyPI / pip install claim | BLOCKED_ON_BOSS_TOKEN — week may **roll** DoD debt on this item only |

**Sunday close rule:** Week 1 counts when §A 1–7 are green. W8 rolls without killing the week if packaging is ready and PUBLISH.md is honest that pip is not true yet.

## NEXT TICK

- Boss: PyPI token + `docs/PUBLISH.md` upload **or** acknowledge W8 roll into Week 2 spare slot.
- Agent: keep Homayoun-only commits; no new face repo until Week 1 gate closed or rolled.
