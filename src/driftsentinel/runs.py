"""A judge run: one judge configuration scoring the anchor set at one point in time.

The `fingerprint` (model id + prompt sha) is what "pin your judge" means in
practice. Two runs with different fingerprints were graded by different
rulers, and any score movement between them is suspect by default.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class JudgeRun:
    """One scoring pass. `anchor_scores` maps anchor id -> the judge's label."""

    model: str
    prompt_sha: str
    anchor_scores: dict[str, str]
    live_metric: float | None = None
    created: str = ""
    source: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("run is missing a judge model id")
        if not self.anchor_scores:
            raise ValueError("run has no anchor scores")

    @property
    def fingerprint(self) -> str:
        return f"{self.model}@{self.prompt_sha or 'unversioned'}"


def _parse_metric(path: str | Path, metric: object) -> float | None:
    if metric is None:
        return None
    if isinstance(metric, bool) or not isinstance(metric, (int, float)):
        raise ValueError(f"run {path}: live_metric must be a number, got {metric!r}")
    value = float(metric)
    if not math.isfinite(value):
        raise ValueError(f"run {path}: live_metric must be a finite number, got {metric!r}")
    return value


def load_run(path: str | Path) -> JudgeRun:
    """Load a run from JSON.

    Expected shape:
        {
          "judge": {"model": "...", "prompt_sha": "..."},
          "created": "2026-08-03",
          "anchor_scores": {"a01": "pass", ...},
          "live_metric": 0.81            # optional: your live eval-suite score
        }
    """
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError(f"run {path}: expected a JSON object, got {type(record).__name__}")
    judge = record.get("judge", {})
    if not isinstance(judge, dict):
        raise ValueError(f"run {path}: 'judge' must be an object with model and prompt_sha")
    scores = record.get("anchor_scores", {})
    if not isinstance(scores, dict):
        raise ValueError(f"run {path}: 'anchor_scores' must be an object of anchor id -> label")
    return JudgeRun(
        model=str(judge.get("model", "")),
        prompt_sha=str(judge.get("prompt_sha", "")),
        anchor_scores={str(k): str(v) for k, v in scores.items()},
        live_metric=_parse_metric(path, record.get("live_metric")),
        created=str(record.get("created", "")),
        source=str(path),
    )
