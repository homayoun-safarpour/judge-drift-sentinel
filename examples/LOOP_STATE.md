# Example backlog — drift gate + agent-loop-engine

Snippet for hiring engineers: wire
[`agent-loop-engine`](https://github.com/homayoun-safarpour/agent-loop-engine)
so a red **judge** ruler blocks new work (**repair beats progress**).

```bash
loop-engine tick --state examples/LOOP_STATE.md \
  --gate "tests=python -m pytest -q" \
  --gate "drift=python examples/as_loop_gate.py --anchors examples/anchors.jsonl --baseline examples/run_baseline.json --current examples/run_current_system.json"
```

Use `examples/as_loop_gate.py` (not raw `drift-sentinel check`) so
`SYSTEM_CHANGE` (exit 3) stays gate-green while `JUDGE_DRIFT` (exit 2)
stays gate-red. See README § "Gate for agent-loop-engine".

- [x] G1 Pin baseline + freeze anchors (cost: S) (touched: 2026-08-04)
- [ ] G2 Run weekly re-score through the drift gate (cost: S) (touched: 2026-08-04)
- [ ] G3 On JUDGE_DRIFT, re-pin judge / repair prompt before features (cost: M)
