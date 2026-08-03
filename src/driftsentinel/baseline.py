"""Pin a scored run as the frozen baseline for later drift checks.

A pinned baseline is a normal run JSON plus the anchor set's `freeze_hash`
and the kappa against the human labels at pin time. Later `check` calls
compare a current run to this artifact; W2 will refuse to check if the
anchor file no longer matches the recorded hash.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from driftsentinel.agreement import cohen_kappa
from driftsentinel.anchors import AnchorSet
from driftsentinel.runs import JudgeRun


def _require_full_coverage(anchors: AnchorSet, run: JudgeRun) -> None:
    missing = anchors.ids() - set(run.anchor_scores)
    if missing:
        names = ", ".join(sorted(missing)[:5])
        raise ValueError(
            f"run {run.source or run.fingerprint} did not score every anchor "
            f"(missing {len(missing)}: {names}). A partial re-score cannot be pinned."
        )


def pin_baseline(anchors: AnchorSet, run: JudgeRun) -> dict[str, Any]:
    """Score `run` against `anchors` and return a freeze-ready baseline payload."""
    _require_full_coverage(anchors, run)
    kappa = cohen_kappa(anchors.labels, run.anchor_scores)
    payload: dict[str, Any] = {
        "judge": {"model": run.model, "prompt_sha": run.prompt_sha},
        "created": run.created,
        "anchor_scores": dict(run.anchor_scores),
        "anchor_freeze_hash": anchors.freeze_hash,
        "baseline_kappa": round(kappa, 6),
        "pinned": True,
    }
    if run.live_metric is not None:
        payload["live_metric"] = run.live_metric
    return payload


def write_baseline(path: str | Path, payload: dict[str, Any]) -> Path:
    """Write a pinned baseline JSON to disk. Returns the path written."""
    out = Path(path)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
