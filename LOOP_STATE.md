# judge-drift-sentinel : project backlog

Bounded engineering backlog for this repository. One checkbox per increment.

- [x] W1 `drift-sentinel baseline` command: score a run and freeze it as the pinned baseline (cost: S) (touched: 2026-08-03)
- [x] W2 Anchor freeze-hash enforcement: `check` refuses to run if the anchor file no longer matches the hash recorded in the baseline (cost: S) (touched: 2026-08-03)
- [x] W3 Weighted kappa for ordinal rubrics (0-3 scales, not just pass/fail) (cost: M) (touched: 2026-08-04)
- [x] W4 `drift-sentinel history`: verdict timeline across N run files, spot slow decay (cost: M) (touched: 2026-08-04)
- [x] W5 GitHub Actions example: weekly anchor re-score, open an issue on JUDGE_DRIFT (cost: M) (touched: 2026-08-04)
- [x] W6 Adapter: read anchor scores straight from a judge-reliability-kit panel export (cost: M) (touched: 2026-08-04)
- [x] W7 Docs: wiring `drift-sentinel check` as an agent-loop-engine gate (cost: S) (touched: 2026-08-04)
- [x] W8 Publish to PyPI so `pip install judge-drift-sentinel` is true (cost: M) (touched: 2026-08-05)
  - Done: PyPI `judge-drift-sentinel==0.1.0`; install path verified 2026-08-05.
- [x] Community GFI #9: named pytest for `examples/drifting` history exit 2 (cost: S) (touched: 2026-08-09)
  - Done: `tests/test_history_example.py::test_examples_drifting_history_exits_2_with_judge_drift`.
- [x] Packaging: `[project.optional-dependencies] dev` (`pytest`, `ruff`) so README `pip install -e ".[dev]"` is true (cost: S) (touched: 2026-08-10)
  - Done: `pyproject.toml` extras + `tests/test_packaging.py`.
- [x] Adapter audit: lock panel-envelope fields + documented `import-judgekit` CLI flags against `examples/judgekit_panel_export.json` (cost: S) (touched: 2026-08-11)
  - Done: `tests/test_adapter.py::test_import_judgekit_cli_locks_panel_envelope_and_documented_flags`.

## Release gate

| # | Check | Status |
| --- | --- | --- |
| 1 | CI green on Python 3.10 / 3.11 / 3.12 | PASS |
| 2 | Named claim tests + pytest green | PASS |
| 3 | Worked example produces real output | PASS |
| 4 | Fresh clone path under 30 minutes from README | PASS |
| 5 | README claims match named tests | PASS |
| 6 | Interview notes (`docs/INTERVIEW.md`) | PASS |
| 7 | PyPI install claim (`0.1.0`) | PASS |

## Next

- Keep CI gate docs current as sibling instruments change (weekly re-score workflow + loop-engine gate).
- Optional later: richer ordinal rubrics and more panel-export formats.

## Maintenance log

- 2026-08-11: Adapter audit - named claim for panel envelope + documented `import-judgekit` flags vs `examples/judgekit_panel_export.json`; README judgekit section + encoding cleanup; pytest 66, ruff clean.
- 2026-08-10: Added `[project.optional-dependencies] dev` (`pytest`, `ruff`); named claim in `tests/test_packaging.py`; pytest 65, ruff clean.
- 2026-08-09: Shipped GFI #9 named pytest for `examples/drifting` history (`test_history_example.py`); pytest 63, ruff clean.
- 2026-08-09: Sunday gate refresh — CI run 31270926978, pytest 62, worked example JUDGE_DRIFT exit 2, public_git_guard PASS; growth pulse logged.
- 2026-08-08: Restored BENCHMARK GATE after accidental trim; linked community GFI #7 from Next + README Contributing.
- 2026-08-07: Interview/README/LOOP em-dash cleanup; topics confirmed; CI green on latest docs push. Week backlog W1-W8 remains complete. Next focus: Sunday 2026-08-10 benchmark gate paste + LinkedIn draft (Boss).

## BENCHMARK GATE
Week: Mon 2026-08-04 to Sun 2026-08-10 · repo: judge-drift-sentinel

| Check | Result | Evidence |
| --- | --- | --- |
| CI 3.10/3.11/3.12 | PASS | https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/runs/31283081576 |
| Named claim tests | PASS | local `pytest -q` -> 63 passed (2026-08-09; includes drifting history fixture) |
| Worked example | PASS | `baseline` then `check` on examples/{anchors.jsonl,run_baseline.json,run_current.json} -> JUDGE_DRIFT exit 2 (kappa 0.833->0.333) |
| Fork/implement <30 min | PASS | clean clone+pip install -e .+baseline+check = 22s (2026-08-07); expected JUDGE_DRIFT |
| public_git_guard | PASS | PASS on 2026-08-09 Sunday close |
| README AI-tell clean | PASS | guard C clean after Quickstart path fix (643f239) |
| Interview pack | PASS | docs/INTERVIEW.md present |

Field/external benchmark (§B): not claimed this week.

Sunday close 2026-08-09: gate evidence refreshed above; growth pulse wrote 11 face rows; LinkedIn paste remains Boss-only (`D:\live_memory\LINKEDIN_DRAFT_2026-08-08_ireland_jobs.md`). Community: GFI #9 shipped (named pytest); close the GitHub issue when convenient.

## NEXT TICK (evening 2026-08-13)

- **Item:** Audit `.github/workflows/weekly-anchor-rescore.yml` + README CI section against `tests/test_weekly_rescore_workflow.py` and add/adjust a named claim if any documented trigger, input, or JUDGE_DRIFT issue path is untested.
- **Why:** Gates green on main (CI 31471748435); W1–W8 and adapter envelope claims are landed. Remaining Next head is keeping the weekly CI / loop-engine gate docs accurate—no new product scope.
- **Verify:** `python -m ruff check src tests && python -m pytest -q tests/test_weekly_rescore_workflow.py tests/test_loop_engine_gate_docs.py`

