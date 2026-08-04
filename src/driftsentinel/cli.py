"""drift-sentinel: the command-line interface.

`drift-sentinel check` exits 0 when your eval numbers are trustworthy
(STABLE), 3 on SYSTEM_CHANGE (trustworthy, but your system moved), and 2 on
JUDGE_DRIFT (do not trust the numbers). That makes it usable as a quality
gate: fail the pipeline precisely when the scoreboard itself is broken.

`drift-sentinel baseline` scores a run against the frozen anchors and writes
a pinned baseline JSON (with `anchor_freeze_hash`) for later `check` calls.

`drift-sentinel history` walks N ordered runs, prints the verdict + kappa
timeline, and flags slow decay that no single pairwise `check` would catch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from driftsentinel.agreement import WEIGHT_SCHEMES, KappaConfig
from driftsentinel.anchors import load_anchors
from driftsentinel.baseline import (
    enforce_anchor_freeze,
    load_recorded_freeze_hash,
    pin_baseline,
    write_baseline,
)
from driftsentinel.history import HistoryReport, build_history
from driftsentinel.runs import load_run
from driftsentinel.verdict import Verdict, diagnose


def _parse_kappa_levels(raw: str | None) -> tuple[int, ...] | None:
    if raw is None or raw.strip() == "":
        return None
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise ValueError("--kappa-levels must be a comma-separated list of integers, e.g. 0,1,2,3")
    try:
        return tuple(int(p) for p in parts)
    except ValueError as exc:
        raise ValueError(
            "--kappa-levels must be a comma-separated list of integers, e.g. 0,1,2,3"
        ) from exc


def _kappa_config_from_args(args: argparse.Namespace) -> KappaConfig:
    return KappaConfig(
        weights=args.kappa_weights,
        levels=_parse_kappa_levels(args.kappa_levels),
    )


def _add_kappa_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--kappa-weights",
        choices=sorted(WEIGHT_SCHEMES),
        default="none",
        help=(
            "kappa weight scheme: none (default, binary/categorical), "
            "linear or quadratic (ordinal 0-3 rubrics)"
        ),
    )
    parser.add_argument(
        "--kappa-levels",
        default=None,
        help="comma-separated ordinal scale when using weighted kappa (e.g. 0,1,2,3)",
    )


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
    _add_kappa_args(check)
    check.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    baseline = sub.add_parser(
        "baseline",
        help="score a run and freeze it as the pinned baseline",
    )
    baseline.add_argument("--anchors", required=True, help="anchor set JSONL (id, label per line)")
    baseline.add_argument("--run", required=True, help="judge run JSON to pin as baseline")
    baseline.add_argument("--out", required=True, help="path to write the pinned baseline JSON")
    _add_kappa_args(baseline)
    baseline.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    history = sub.add_parser(
        "history",
        help="verdict timeline across N runs; flag slow kappa decay",
    )
    history.add_argument("--anchors", required=True, help="anchor set JSONL (id, label per line)")
    history.add_argument(
        "--runs",
        nargs="+",
        required=True,
        metavar="RUN",
        help="ordered run/baseline JSON files (oldest first; at least two)",
    )
    history.add_argument("--kappa-drop", type=float, default=0.10,
                         help="kappa drop that declares JUDGE_DRIFT / slow decay (default 0.10)")
    history.add_argument("--metric-shift", type=float, default=0.05,
                         help="live-metric shift that declares SYSTEM_CHANGE (default 0.05)")
    _add_kappa_args(history)
    history.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def _cmd_check(args: argparse.Namespace) -> int:
    anchors = load_anchors(args.anchors)
    enforce_anchor_freeze(anchors, load_recorded_freeze_hash(args.baseline))
    baseline = load_run(args.baseline)
    current = load_run(args.current)
    verdict = diagnose(
        anchors,
        baseline,
        current,
        kappa_drop=args.kappa_drop,
        metric_shift=args.metric_shift,
        kappa=_kappa_config_from_args(args),
    )
    print(_render_json(verdict) if args.json else _render_plain(verdict))
    return verdict.exit_code


def _cmd_baseline(args: argparse.Namespace) -> int:
    anchors = load_anchors(args.anchors)
    run = load_run(args.run)
    payload = pin_baseline(
        anchors,
        run,
        kappa=_kappa_config_from_args(args),
    )
    written = write_baseline(args.out, payload)
    if args.json:
        print(json.dumps({**payload, "wrote": str(written)}, indent=2))
    else:
        print(_render_baseline_plain(payload, str(written)))
    return 0


def _short_path(path: str) -> str:
    return Path(path).name or path


def _render_history_plain(report: HistoryReport) -> str:
    lines: list[str] = []
    for step in report.steps:
        v = step.verdict
        lines.append(
            f"step {step.index:<3} {_short_path(step.from_source)} -> "
            f"{_short_path(step.to_source):<24} {v.kind:<14} "
            f"kappa {v.baseline_kappa:.3f} -> {v.current_kappa:.3f}"
        )
    lines.append("---")
    lines.append(
        f"window kappa : {report.first_kappa:.3f} -> {report.last_kappa:.3f} "
        f"(drop {report.cumulative_kappa_drop:+.3f})"
    )
    if report.slow_decay:
        lines.append(f"slow decay   : YES — {report.slow_decay_reason}")
    else:
        lines.append("slow decay   : no")
    lines.extend(f"note         : {note}" for note in report.notes)
    return "\n".join(lines)


def _render_history_json(report: HistoryReport) -> str:
    payload = {
        "steps": [
            {
                "index": step.index,
                "from": step.from_source,
                "to": step.to_source,
                "verdict": step.verdict.kind,
                "baseline_kappa": round(step.verdict.baseline_kappa, 6),
                "current_kappa": round(step.verdict.current_kappa, 6),
                "anchor_flip_rate": round(step.verdict.anchor_flip_rate, 6),
                "metric_delta": step.verdict.metric_delta,
                "reason": step.verdict.reason,
            }
            for step in report.steps
        ],
        "first_kappa": round(report.first_kappa, 6),
        "last_kappa": round(report.last_kappa, 6),
        "cumulative_kappa_drop": round(report.cumulative_kappa_drop, 6),
        "slow_decay": report.slow_decay,
        "slow_decay_reason": report.slow_decay_reason,
        "notes": list(report.notes),
        "exit_code": report.exit_code,
    }
    return json.dumps(payload, indent=2)


def _cmd_history(args: argparse.Namespace) -> int:
    anchors = load_anchors(args.anchors)
    # Enforce freeze hash from the first file when it is a pinned baseline.
    enforce_anchor_freeze(anchors, load_recorded_freeze_hash(args.runs[0]))
    runs = [load_run(path) for path in args.runs]
    report = build_history(
        anchors,
        runs,
        kappa_drop=args.kappa_drop,
        metric_shift=args.metric_shift,
        kappa=_kappa_config_from_args(args),
    )
    print(_render_history_json(report) if args.json else _render_history_plain(report))
    return report.exit_code


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "baseline":
            return _cmd_baseline(args)
        if args.command == "history":
            return _cmd_history(args)
        return _cmd_check(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
