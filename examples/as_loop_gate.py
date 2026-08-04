#!/usr/bin/env python3
"""Remap `drift-sentinel check` exits for agent-loop-engine gates.

[agent-loop-engine](https://github.com/homayoun-safarpour/agent-loop-engine)
treats `returncode == 0` as PASS and any nonzero as FAIL
(**repair beats progress**). Sentinel's three-way process exits are:

| Verdict         | `drift-sentinel check` | This wrapper | Loop effect                          |
|-----------------|------------------------|--------------|--------------------------------------|
| STABLE          | 0                      | 0            | gate green — advance / unstick OK    |
| SYSTEM_CHANGE   | 3                      | 0            | gate green — ruler held; movement real |
| JUDGE_DRIFT     | 2                      | 2            | gate red — repair the scoreboard     |
| usage / IO error| 1                      | 1            | gate red — fix the wiring            |

Without this remapping, exit 3 (SYSTEM_CHANGE) would look like a red gate
and wrongly block backlog progress even though the ruler is trustworthy.

Copy-paste tick (from this repo root, both CLIs on PATH):

```bash
loop-engine tick --state examples/LOOP_STATE.md \\
  --gate "tests=python -m pytest -q" \\
  --gate "drift=python examples/as_loop_gate.py \\
    --anchors examples/anchors.jsonl \\
    --baseline examples/run_baseline.json \\
    --current examples/run_current_system.json"
```

Pass any `drift-sentinel check` flags after the script name (they are forwarded).
"""

from __future__ import annotations

import sys

from driftsentinel.cli import main as sentinel_main

# Raw sentinel exits that mean "scoreboard is trustworthy" for loop-engine.
_TRUSTWORTHY = frozenset({0, 3})  # STABLE, SYSTEM_CHANGE


def remap_for_loop_engine(sentinel_exit: int) -> int:
    """Map sentinel process exit -> loop-engine pass/fail exit."""
    if sentinel_exit in _TRUSTWORTHY:
        return 0
    return sentinel_exit


def main(argv: list[str] | None = None) -> int:
    args = list(argv if argv is not None else sys.argv[1:])
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__.strip(), file=sys.stderr)
        return 0 if args and args[0] in {"-h", "--help"} else 1
    # Forward as `drift-sentinel check ...`
    if args[0] != "check":
        args = ["check", *args]
    return remap_for_loop_engine(sentinel_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
