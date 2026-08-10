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

- Add `[project.optional-dependencies] dev` (`pytest`, `ruff`) so README `pip install -e ".[dev]"` is true.
- Keep adapter and CI gate docs current as sibling instruments change.
- Optional later: richer ordinal rubrics and more panel-export formats.

## Maintenance log

- 2026-08-10: Sunday usefulness close — CI 31302752262 green; local pytest 63 + ruff clean; worked example JUDGE_DRIFT exit 2; claim still true; LinkedIn draft + Monday NEXT TICK recorded below.
- 2026-08-09: Shipped GFI #9 named pytest for `examples/drifting` history (`test_history_example.py`); pytest 63, ruff clean.
- 2026-08-09: Sunday gate refresh — CI run 31270926978, pytest 62, worked example JUDGE_DRIFT exit 2, public_git_guard PASS; growth pulse logged.
- 2026-08-08: Restored BENCHMARK GATE after accidental trim; linked community GFI #7 from Next + README Contributing.
- 2026-08-07: Interview/README/LOOP em-dash cleanup; topics confirmed; CI green on latest docs push. Week backlog W1-W8 remains complete.

## BENCHMARK GATE
Week: Mon 2026-08-04 to Sun 2026-08-10 · repo: judge-drift-sentinel

| Check | Result | Evidence |
| --- | --- | --- |
| CI 3.10/3.11/3.12 | PASS | https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/runs/31302752262 |
| Named claim tests | PASS | local `pytest -q` -> 63 passed (2026-08-10; includes drifting history fixture) |
| Worked example | PASS | `baseline` then `check` on examples/{anchors.jsonl,run_baseline.json,run_current.json} -> JUDGE_DRIFT exit 2 (kappa 0.833->0.333) |
| Fork/implement <30 min | PASS | clean clone+pip install -e .+baseline+check = 22s (2026-08-07); expected JUDGE_DRIFT |
| public_git_guard | PASS | no private/SLR markers in LOOP Sunday close; README ban scan clean (2026-08-10) |
| README AI-tell clean | PASS | banned AI-tell phrases absent on scan (2026-08-10) |
| Interview pack | PASS | docs/INTERVIEW.md present |

Field/external benchmark (§B): not claimed this week.

## SUNDAY CLOSE (2026-08-10)

- **CI status:** PASS on main — [run 31302752262](https://github.com/homayoun-safarpour/judge-drift-sentinel/actions/runs/31302752262) (Python 3.10/3.11/3.12). Local: `ruff check src tests` clean; `pytest -q` → 63 passed.
- **Claim still true?** Yes. Frozen-anchor kappa drop still attributes movement to the judge (`tests/test_verdict.py::test_drift_on_frozen_anchors_blames_the_judge_not_the_system`); history slow-decay + drifting fixture still exit 2; PyPI `0.1.0` claim unchanged.
- **Example still runnable?** Yes. `drift-sentinel baseline` on `examples/run_baseline.json` pins kappa 0.833 / freeze `ca7c25804843`; `check` vs `run_current.json` → JUDGE_DRIFT exit 2 (0.833→0.333); `run_current_system.json` → SYSTEM_CHANGE exit 3.
- **Week backlog:** W1–W8 complete; GFI #9 named pytest shipped (issue #9 still open on GitHub — close when convenient).
- **LinkedIn 5-bullet draft** (field pain first; public claims only; Boss pastes):
  1. When an LLM-judge eval score drops after a provider model update, teams often cannot tell whether the system regressed or the judge moved — the dashboard shows the same artifact either way.
  2. The expensive mistake is rolling back a healthy deploy (or chasing a phantom regression) because the ruler changed behind a `-latest` alias or a quiet prompt edit.
  3. `judge-drift-sentinel` freezes a small human-labeled anchor set and re-scores it every run: if agreement with those humans falls, the verdict is JUDGE_DRIFT, not “your app broke.”
  4. One CLI, three outcomes with CI exit codes — STABLE / SYSTEM_CHANGE / JUDGE_DRIFT — zero LLM calls, stdlib-only, so the gate is deterministic in milliseconds.
  5. Shipped path: `pip install judge-drift-sentinel` (0.1.0), worked examples in-repo, and a weekly GitHub Actions re-score that opens an issue when the ruler itself drifts.

## NEXT TICK (sunday 2026-08-10)

Week boundary: retarget active week to **Mon 2026-08-11 → Sun 2026-08-17** on next Monday scaffold. Carry forward the open contributor-path gap as the first Monday tick:

- **Item:** Add `[project.optional-dependencies] dev = ["pytest", "ruff"]` in `pyproject.toml` so README `pip install -e ".[dev]"` installs the contributor toolchain.
- **Why:** README already documents that path; the extras table is missing, so a fresh clone following Contributing cannot rely on `.[dev]`.
- **Verify:** `python -m pip install -e ".[dev]" && python -m ruff check src tests && python -m pytest -q`
- **Also:** Close GitHub issue #9 if the named pytest lock is accepted as done; keep adapter/CI gate docs current as sibling instruments change.

