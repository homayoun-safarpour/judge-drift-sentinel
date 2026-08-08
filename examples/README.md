# Examples — Fixture Map

This table maps each fixture file to the drift scenario it demonstrates.

| Fixture | Drift story | What to look for |
|---------|-------------|------------------|
| `run_current.json` | **JUDGE_DRIFT** — intentional | Kappa drop against frozen anchors; system outputs unchanged |
| `run_current_system.json` | **SYSTEM_DRIFT** — system-side | Kappa stable; system outputs changed |
| `synthetic_judge_only_current.json` | **Judge-only attribution** | Minimal fixture isolating judge movement |
| `synthetic_judge_only_OUTPUT.txt` | **Expected output** | Reference output for judge-only scenario |
| `anchors.jsonl` | **Frozen anchor set** | Human-labeled examples that never change |
| `as_loop_gate.py` | **Exit remap** | Agent-loop-engine integration hook |

## How to use

```bash
# Run the check against a baseline
drift-sentinel check --baseline examples/run_baseline.json --current examples/run_current.json

# See judge-only attribution
drift-sentinel check --baseline examples/run_baseline.json --current examples/synthetic_judge_only_current.json
```

See the [worked example](../README.md#worked-example) in the main README for a step-by-step walkthrough.
