# Drifting History Example

This directory contains a sequence of judge runs showing a steady decay in agreement (kappa) with human anchors, triggering a `JUDGE_DRIFT` verdict across the timeline.

Run the history check from the repository root:

```bash
drift-sentinel history \
  --anchors examples/drifting/anchors.jsonl \
  --runs examples/drifting/run_1.json examples/drifting/run_2.json examples/drifting/run_3.json
```

**Expected Exit Code**: `1` (indicating judge drift detected).
