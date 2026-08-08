# Examples

One-screen map of the fixtures under this directory. Use these to see the difference between **judge drift** and **system-side drift** without any live model calls.

| Fixture | Story |
|---|---|
| `run_current.json` | Intentional **JUDGE_DRIFT** (kappa vs humans fell; distrust the scoreboard). |
| `run_current_system.json` | **SYSTEM_CHANGE** / system-side drift (kappa held, live metric moved; the movement is real). |
| `synthetic_judge_only_*.json` / `synthetic_judge_only_OUTPUT.txt` | Judge-only attribution: drift isolated to the judge, not the system under test. |
| `as_loop_gate.py` | Exit remap for [agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine) gates (`SYSTEM_CHANGE` → pass, `JUDGE_DRIFT` → fail). |
| `drifting/` | Multi-run **history** fixture (consecutive pairs report `JUDGE_DRIFT`; expected exit `2`). |

Supporting files: `anchors.jsonl` (frozen human labels), `run_baseline.json` (pinned baseline run), `LOOP_STATE.md` (sample loop backlog).

Quick check from the repo root:

```bash
drift-sentinel check \
  --anchors examples/anchors.jsonl \
  --baseline examples/run_baseline.json \
  --current examples/run_current.json
```

History (slow / multi-step drift):

```bash
drift-sentinel history \
  --anchors examples/drifting/anchors.jsonl \
  --runs examples/drifting/run_1.json examples/drifting/run_2.json examples/drifting/run_3.json
# expect exit 2
```

See the [worked example](../README.md#worked-example-real-output) in the main README for full expected output.
