"""drift-sentinel: the command-line interface.

`drift-sentinel check` exits 0 when your eval numbers are trustworthy
(STABLE), 3 on SYSTEM_CHANGE (trustworthy, but your system moved), and 2 on
JUDGE_DRIFT (do not trust the numbers). That makes it usable as a quality
gate: fail the pipeline precisely when the scoreboard itself is broken.

`drift-sentinel baseline` scores a run against the frozen anchors and writes
a pinned baseline JSON (with `anchor_freeze_hash`) for later `check` calls.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from driftsentinel.anchors import load_anchors
from driftsentinel.baseline import pin_baseline, write_baseline
from driftsentinel.runs import load_run
from driftsentinel.verdict import Verdict, diagnose


def _render_plain(verdict: Verdict) -> str:
    pin = (
        "held " + verdict.current_fingerprint
        if verdict.judge_pinned
        else f"CHANGED {verdict.baseline_fingerprint} -> {verdict.current_fingerprint}"
    )
    lines = [
        f"verdict      : {verdict.kind}",
        f"anchor kappa : {verdict.baseline_kappa:.3f} -> {verdict.current_kappa:.3f}",
        f"anchor flips : {verdict.anchor_flip_rate:.1%} of frozen anchors changed label",
        f"judge pin    : {pin}",
    ]
    if verdict.metric_delta is not None:
        lines.append(f"live metric  : moved {verdict.metric_delta:+.3f}")
    lines.append(f"reason       : {verdict.reason}")
    lines.extend(f"note         : {note}" for note in verdict.notes)
    return "\n".join(lines)


def _render_json(verdict: Verdict) -> str:
    payload = {
        "verdict": verdict.kind,
        "reason": verdict.reason,
        "baseline_kappa": round(verdict.baseline_kappa, 6),
        "current_kappa": round(verdict.current_kappa, 6),
        "anchor_flip_rate": round(verdict.anchor_flip_rate, 6),
        "judge_pinned": verdict.judge_pinned,
        "baseline_fingerprint": verdict.baseline_fingerprint,
        "current_fingerprint": verdict.current_fingerprint,
        "metric_delta": verdict.metric_delta,
        "notes": list(verdict.notes),
        "exit_code": verdict.exit_code,
    }
    return json.dumps(payload, indent=2)


def _render_baseline_plain(payload: dict[str, Any], out_path: str) -> str:
    judge = payload["judge"]
    fingerprint = f"{judge['model']}@{judge['prompt_sha'] or 'unversioned'}"
    lines = [
        "pinned       : yes",
        f"anchor kappa : {payload['baseline_kappa']:.3f}",
        f"freeze hash  : {payload['anchor_freeze_hash']}",
        f"judge pin    : {fingerprint}",
        f"wrote        : {out_path}",
    ]
    if "live_metric" in payload:
        lines.insert(4, f"live metric  : {payload['live_metric']:.3f}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="drift-sentinel",
        description="Attribute eval-score movement to your system or to your LLM judge.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="compare two judge runs over one frozen anchor set")
    check.add_argument("--anchors", required=True, help="anchor set JSONL (id, label per line)")
    check.add_argument("--baseline", required=True, help="baseline run JSON")
    check.add_argument("--current", required=True, help="current run JSON")
    check.add_argument("--kappa-drop", type=float, default=0.10,
                       help="kappa drop that declares JUDGE_DRIFT (default 0.10)")
    check.add_argument("--metric-shift", type=float, default=0.05,
                       help="live-metric shift that declares SYSTEM_CHANGE (default 0.05)")
    check.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    baseline = sub.add_parser(
        "baseline",
        help="score a run and freeze it as the pinned baseline",
    )
    baseline.add_argument("--anchors", required=True, help="anchor set JSONL (id, label per line)")
    baseline.add_argument("--run", required=True, help="judge run JSON to pin as baseline")
    baseline.add_argument("--out", required=True, help="path to write the pinned baseline JSON")
    baseline.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    anchors = load_anchors(args.anchors)
    baseline = load_run(args.baseline)
    current = load_run(args.current)
    verdict = diagnose(
        anchors,
        baseline,
        current,
        kappa_drop=args.kappa_drop,
        metric_shift=args.metric_shift,
    )
    print(_render_json(verdict) if args.json else _render_plain(verdict))
    return verdict.exit_code


def _cmd_baseline(args: argparse.Namespace) -> int:
    anchors = load_anchors(args.anchors)
    run = load_run(args.run)
    payload = pin_baseline(anchors, run)
    written = write_baseline(args.out, payload)
    if args.json:
        print(json.dumps({**payload, "wrote": str(written)}, indent=2))
    else:
        print(_render_baseline_plain(payload, str(written)))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "baseline":
            return _cmd_baseline(args)
        return _cmd_check(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
