# Reliability card — judge-drift-sentinel

| Field | Value |
| --- | --- |
| **Job** | Attribute eval-score movement to judge drift vs system change vs noise |
| **Primary metrics** | Cohen's kappa vs frozen human anchors (optional linear/quadratic weights) |
| **Named verdicts** | `STABLE` (0), `JUDGE_DRIFT` (2), `SYSTEM_CHANGE` (3); config errors exit 1 |
| **Fixtures** | `examples/anchors.jsonl`, `examples/run_baseline.json`, `examples/run_current.json`, `examples/synthetic_judge_only_current.json` |
| **Central test** | `tests/test_verdict.py::test_drift_on_frozen_anchors_blames_the_judge_not_the_system` |
| **Runtime deps for core claim** | stdlib only; **no LLM calls** at check time |
| **Claim** | With frozen human anchors, a kappa drop isolates the judge |
| **Not claimed** | Replaces human labeling; explains *why* a provider model changed; RewardBench rank |

## Field alignment (not affiliation)

Same instinct as living / meta-eval practice: **frozen references beat moving scoreboards.**
Companion to `judge-reliability-kit` (panel disagreement now) vs this package (score movement over time).
