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
- [x] CI audit: lock weekly-anchor-rescore triggers, path inputs, and JUDGE_DRIFT issue path against README (cost: S) (touched: 2026-08-17)
  - Done: `tests/test_weekly_rescore_workflow.py::test_weekly_rescore_workflow_opens_issue_on_judge_drift`.
- [x] Loop-engine gate audit: lock README remapper table + tick command + `examples/LOOP_STATE.md` snippet + STABLE/SYSTEM_CHANGE/JUDGE_DRIFT wrapper exits (cost: S) (touched: 2026-08-20)
  - Done: `tests/test_loop_engine_gate_docs.py` (4 named claims).

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

- [x] Optional: richer ordinal rubrics (named claim for linear vs quadratic near-miss separation beyond the existing weighted-kappa test) (cost: S) (touched: 2026-08-21)
  - Done: `tests/test_agreement.py::test_quadratic_penalizes_far_misses_more_than_linear`.
- [x] Document and lock that only `judgekit.panel_export/v1` (plus bare ratings + gold) is supported; reject unknown schema_version (cost: S) (touched: 2026-08-22)
  - Done: `tests/test_adapter.py::test_unsupported_panel_schema_version_is_rejected`.
- [x] Named claim locking `import-judgekit --help` to the v1-only schema gate (cost: S) (touched: 2026-08-23)
  - Done: `tests/test_adapter.py::test_import_judgekit_help_locks_v1_only_schema_gate`.
- [x] Named claim locking adapter unsupported-schema `ValueError` text to the same v1-only / bare-ratings escape hatch as `import-judgekit --help` (cost: S) (touched: 2026-08-24)
  - Done: `tests/test_adapter.py::test_unsupported_schema_error_locks_v1_only_escape_hatch`.
- [x] Named claim locking unrecognized-panel `ValueError` text to the same v1-only / bare-ratings contract as the unsupported-schema error and `import-judgekit --help` (cost: S) (touched: 2026-08-25)
  - Done: `tests/test_adapter.py::test_unrecognized_panel_error_locks_v1_only_escape_hatch`.
- [x] Named claim that unsupported-schema and unrecognized-panel `ValueError` strings share the same operator-facing phrase set (`only {SCHEMA_VERSION} is supported`, `bare ratings`, `human_labels`) (cost: S) (touched: 2026-08-26)
  - Done: `tests/test_adapter.py::test_schema_and_unrecognized_errors_share_escape_hatch_phrases`.
- [x] Named claim that `import-judgekit --help` shares the same operator-facing phrase set (SCHEMA_VERSION / v1 citation, `bare ratings`, human-labels / `--human-labels`) with both unsupported-schema and unrecognized-panel `ValueError` strings (cost: S) (touched: 2026-08-27)
  - Done: `tests/test_adapter.py::test_help_and_raise_paths_share_escape_hatch_phrases`.
- [x] Named claim that `import-judgekit` CLI stderr surfaces the shared escape-hatch phrases (`only {SCHEMA_VERSION} is supported`, `bare ratings`, `human_labels`) and exits 1 when the panel is unsupported-schema or unrecognized (cost: S) (touched: 2026-08-28)
  - Done: `tests/test_adapter.py::test_import_judgekit_cli_stderr_shares_escape_hatch_phrases`.
- [x] Named claim that `import-judgekit` CLI rejects malformed panel JSON (`JSONDecodeError`) with exit 1 and an `error:` stderr line (cost: S) (touched: 2026-08-29)
  - Done: `tests/test_adapter.py::test_import_judgekit_cli_rejects_malformed_panel_json`.
- [x] Named claim that `import-judgekit` CLI rejects a missing panel file (`OSError` / `FileNotFoundError`) with exit 1 and an `error:` stderr line (cost: S) (touched: 2026-08-30)
  - Done: `tests/test_adapter.py::test_import_judgekit_cli_rejects_missing_panel_file`.
- [x] Named claim that `import-judgekit` CLI rejects a missing `--human-labels` file (`OSError` / `FileNotFoundError`) with exit 1 and an `error:` stderr line when bare ratings require separate gold (cost: S) (touched: 2026-08-31)
  - Done: `tests/test_adapter.py::test_import_judgekit_cli_rejects_missing_human_labels_file`.
- Optional later: more panel-export formats beyond `judgekit.panel_export/v1` (when a real second producer exists).

## Maintenance log

- 2026-08-31: import-judgekit CLI missing-human-labels claim - named test asserts a missing `--human-labels` path (bare ratings) prints `error:` on stderr, exits 1, writes no outputs, and does not dump a traceback; README cites the claim; pytest 78, ruff clean.
- 2026-08-30: import-judgekit CLI missing-panel claim - named test asserts a missing `--panel` path prints `error:` on stderr, exits 1, writes no outputs, and does not dump a traceback; README cites the claim; pytest 77, ruff clean.
- 2026-08-29: import-judgekit CLI malformed-JSON claim - named test asserts malformed panel JSON prints `error:` on stderr, exits 1, writes no outputs, and does not dump a traceback; README cites the claim; pytest 76, ruff clean.
- 2026-08-28: import-judgekit CLI stderr escape-hatch claim - named test asserts unsupported-schema and unrecognized panel files print shared phrases on stderr and exit 1; README cites the claim; pytest 75, ruff clean.
- 2026-08-27: help+raise shared escape-hatch claim - named test asserts `import-judgekit --help` and both ValueError paths share SCHEMA_VERSION / v1 citation, `bare ratings`, and human-labels / `--human-labels`; README cites the claim; pytest 74, ruff clean.
- 2026-08-26: shared escape-hatch phrase claim - named test asserts unsupported-schema and unrecognized-panel ValueErrors both carry `only {SCHEMA_VERSION} is supported`, `bare ratings`, and `human_labels`; README cites the claim; pytest 73, ruff clean.
- 2026-08-25: unrecognized-panel ValueError claim - named test locks malformed-panel parse error to v1-only / bare ratings + human_labels escape hatch aligned with unsupported-schema and `--help`; README cites the claim; pytest 72, ruff clean.
- 2026-08-24: unsupported-schema ValueError claim - named test locks parse error text to v1-only / omit-schema / bare ratings + human_labels escape hatch aligned with `--help`; README cites the claim; pytest 71, ruff clean.
- 2026-08-23: import-judgekit help claim - named test locks `--help` to v1-only / unknown schema_version rejected / bare ratings + `--human-labels`; README cites the claim; pytest 70, ruff clean.
- 2026-08-22: Panel schema gate - adapter rejects unknown `schema_version` values; README + CLI help state v1-only; named claim `test_unsupported_panel_schema_version_is_rejected`; pytest 69, ruff clean.
- 2026-08-21: Ordinal kappa depth - named claim that quadratic opens a larger near-vs-far gap than linear on the same pair; README ordinal flags cite the test; pytest 68, ruff clean.
- 2026-08-20: Loop-engine gate audit - named claims lock README remapper table, documented tick/state paths, `examples/LOOP_STATE.md` snippet alignment, `_TRUSTWORTHY` remapper, and STABLE/SYSTEM_CHANGE/JUDGE_DRIFT wrapper exits; pytest 67, ruff clean.
- 2026-08-17: Weekly CI audit - named claim locks Monday cron, workflow_dispatch inputs, JUDGE_DRIFT issue title/comment path, exit-2 gate, and schedule defaults; pytest 66, ruff clean.
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

## NEXT TICK (daily 2026-08-31)

- **Item:** Named claim that `import-judgekit` CLI rejects malformed `--human-labels` JSON (`JSONDecodeError`) with exit 1 and an `error:` stderr line when bare ratings require separate gold, so the secondary gold path cannot silently succeed on bad gold JSON.
- **Why:** Missing `--panel` and missing `--human-labels` OSError surfaces are locked; malformed gold JSON is the remaining operator footgun on the same `main()` `JSONDecodeError` catch for the secondary path.
- **Verify:** `python3 -m ruff check src tests && python3 -m pytest -q tests/test_adapter.py`

## SUNDAY CLOSE (2026-08-30)

Usefulness gate for the public week repo `judge-drift-sentinel` (closed Mon 2026-08-31 UTC).

| Signal | Result | Evidence |
| --- | --- | --- |
| CI (3.10 / 3.11 / 3.12) | PASS | https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/runs/33370973254 |
| Local pytest + ruff | PASS | `ruff check src tests` clean; `pytest -q` -> 78 passed |
| Claim still true? | YES | Named claims hold: frozen-anchor JUDGE_DRIFT, history slow decay, drifting fixture, judgekit adapter escape-hatch locks through missing panel / missing human-labels CLI surfaces, loop-engine gate docs, weekly rescore workflow, packaging `.[dev]` |
| Example still runnable? | YES | `baseline` then `check` on `examples/{anchors.jsonl,run_baseline.json,run_current.json}` -> JUDGE_DRIFT exit 2 (kappa 0.833 -> 0.333) |
| Release gate table | PASS | Unchanged; PyPI `0.1.0` claim still documented |

Week boundary: W1–W8 + Next increments through missing-`--human-labels` CLI lock are done. No field/employer demand claimed. No private research content in this close.

### LinkedIn draft (5 bullets — field pain first)

1. When an LLM-judge scoreboard moves after a silent provider update, teams still cannot tell judge drift from a real system regression — so they roll back healthy deploys or chase noise.
2. `judge-drift-sentinel` freezes a small human-labeled anchor set and runs a zero-LLM `drift-sentinel check`: STABLE / SYSTEM_CHANGE / JUDGE_DRIFT from score files you already have.
3. Public worked example stays honest: baseline kappa 0.833 → current 0.333 exits 2 with JUDGE_DRIFT when the judge pin slips to `-latest`.
4. This week finished locking the `import-judgekit` operator surface: shared v1-only / bare-ratings escape-hatch phrases on help + raise + stderr, plus fail-closed exit 1 on malformed panel JSON, missing panel, and missing `--human-labels`.
5. Try path: `pip install judge-drift-sentinel` or `pip install -e ".[dev]"`, then the README Quickstart on the repo examples — CI green on 3.10/3.11/3.12.

## NEXT TICK (sunday 2026-08-30)

- **Scaffold / retarget:** Monday active public week repo remains `homayoun-safarpour/judge-drift-sentinel` @ `main` (week Mon 2026-08-31 → Sun 2026-09-06; no retarget).
- **Item:** Named claim that `import-judgekit` CLI rejects malformed `--human-labels` JSON (`JSONDecodeError`) with exit 1 and an `error:` stderr line when bare ratings require separate gold (carried from daily 2026-08-31).
- **Why:** Panel-path JSONDecodeError and both OSError surfaces are locked; bad gold JSON on the secondary path is the remaining silent-success footgun on the same `main()` catch.
- **Verify:** `python3 -m ruff check src tests && python3 -m pytest -q tests/test_adapter.py`
- **Defer:** Extra panel-export formats beyond v1 — only when a real second producer exists.

