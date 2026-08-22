"""Bridge judge-reliability-kit panel ratings into sentinel AnchorSet / JudgeRun.

judge-reliability-kit has no separate "export" file today — its native input is
already JSON ratings::

    {item_id: {judge_id: [label, label, ...]}}

This module documents a thin panel-export envelope (`judgekit.panel_export/v1`)
that adds the human gold labels and judge fingerprint fields sentinel needs,
and converts either that envelope or bare ratings (+ human labels) into
``AnchorSet`` / ``JudgeRun`` without hand-copying scores.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from driftsentinel.anchors import AnchorSet
from driftsentinel.runs import JudgeRun

SCHEMA_VERSION = "judgekit.panel_export/v1"
SUPPORTED_SCHEMA_VERSIONS = frozenset({SCHEMA_VERSION})
AGGREGATES = frozenset({"modal", "first"})


@dataclass(frozen=True)
class PanelExport:
    """Parsed judgekit panel payload ready for sentinel conversion."""

    ratings: dict[str, dict[str, list[str]]]
    human_labels: dict[str, str]
    judges: dict[str, dict[str, str]]
    created: str = ""
    live_metric: float | None = None
    source: str = ""
    schema_version: str = ""


def modal_label(labels: Sequence[Any]) -> str:
    """Majority label for one judge's replicates (same rule as judgekit._modal)."""
    if not labels:
        raise ValueError("cannot take modal of empty label list")
    return str(Counter(labels).most_common(1)[0][0])


def _looks_like_ratings(obj: Any) -> bool:
    if not isinstance(obj, dict) or not obj:
        return False
    for item_val in obj.values():
        if not isinstance(item_val, dict) or not item_val:
            return False
        for reps in item_val.values():
            if not isinstance(reps, (list, tuple)) or not reps:
                return False
    return True


def _normalize_ratings(raw: Mapping[str, Any]) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = {}
    for item_id, per_judge in raw.items():
        if not isinstance(per_judge, Mapping):
            raise ValueError(f"ratings[{item_id!r}] must be an object of judge -> [labels]")
        judges: dict[str, list[str]] = {}
        for judge_id, reps in per_judge.items():
            if not isinstance(reps, (list, tuple)) or not reps:
                raise ValueError(
                    f"ratings[{item_id!r}][{judge_id!r}] must be a non-empty list of labels"
                )
            judges[str(judge_id)] = [str(x) for x in reps]
        out[str(item_id)] = judges
    if not out:
        raise ValueError("ratings are empty")
    return out


def _normalize_human_labels(raw: Mapping[str, Any]) -> dict[str, str]:
    if not raw:
        raise ValueError("human_labels are empty")
    return {str(k): str(v) for k, v in raw.items()}


def parse_panel_dict(
    record: Mapping[str, Any],
    *,
    human_labels: Mapping[str, Any] | None = None,
    source: str = "",
) -> PanelExport:
    """Parse a panel-export dict or bare judgekit ratings object."""
    if "ratings" in record:
        ratings_raw = record["ratings"]
        if not isinstance(ratings_raw, Mapping):
            raise ValueError("'ratings' must be a JSON object")
        schema = str(record.get("schema_version", "") or "")
        if schema and schema not in SUPPORTED_SCHEMA_VERSIONS:
            supported = ", ".join(sorted(SUPPORTED_SCHEMA_VERSIONS))
            raise ValueError(
                f"unsupported panel schema_version {schema!r}; "
                f"only {supported} is supported "
                f"(omit schema_version on a v1-shaped envelope, or pass bare "
                f"ratings + human_labels)"
            )
        labels_src = human_labels if human_labels is not None else record.get("human_labels")
        if not isinstance(labels_src, Mapping):
            raise ValueError(
                "panel export needs 'human_labels' (or pass them separately) "
                "so sentinel can build an AnchorSet"
            )
        judges_raw = record.get("judges") or {}
        if not isinstance(judges_raw, Mapping):
            raise ValueError("'judges' must be a JSON object when present")
        judges = {
            str(jid): {
                "model": str((meta or {}).get("model", jid) if isinstance(meta, Mapping) else jid),
                "prompt_sha": str(
                    (meta or {}).get("prompt_sha", "") if isinstance(meta, Mapping) else ""
                ),
            }
            for jid, meta in judges_raw.items()
        }
        metric = record.get("live_metric")
        return PanelExport(
            ratings=_normalize_ratings(ratings_raw),
            human_labels=_normalize_human_labels(labels_src),
            judges=judges,
            created=str(record.get("created", "")),
            live_metric=float(metric) if metric is not None else None,
            source=source,
            schema_version=schema or SCHEMA_VERSION,
        )

    if _looks_like_ratings(record):
        if human_labels is None:
            raise ValueError(
                "bare judgekit ratings need human_labels "
                "(panel export 'human_labels' or a separate gold map)"
            )
        return PanelExport(
            ratings=_normalize_ratings(record),
            human_labels=_normalize_human_labels(human_labels),
            judges={},
            source=source,
        )

    raise ValueError(
        "unrecognized panel JSON: expected judgekit.panel_export/v1 "
        "({schema_version, human_labels, ratings}; only that schema_version "
        "is supported) or bare ratings {item: {judge: [labels...]}}"
    )


def load_panel_export(
    path: str | Path,
    *,
    human_labels_path: str | Path | None = None,
) -> PanelExport:
    """Load a panel export (or bare ratings) from disk."""
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError(f"{path}: panel JSON must be an object")
    extra: Mapping[str, Any] | None = None
    if human_labels_path is not None:
        gold = json.loads(Path(human_labels_path).read_text(encoding="utf-8"))
        if isinstance(gold, dict) and "human_labels" in gold:
            inner = gold["human_labels"]
            if not isinstance(inner, Mapping):
                raise ValueError(f"{human_labels_path}: 'human_labels' must be an object")
            extra = inner
        elif isinstance(gold, dict):
            extra = gold
        else:
            raise ValueError(f"{human_labels_path}: human labels must be a JSON object")
    return parse_panel_dict(record, human_labels=extra, source=str(path))


def panel_to_anchors(panel: PanelExport) -> AnchorSet:
    """Build the frozen AnchorSet from panel human_labels."""
    return AnchorSet(labels=dict(panel.human_labels), source=panel.source)


def panel_to_run(
    panel: PanelExport,
    judge_id: str,
    *,
    aggregate: str = "modal",
    model: str | None = None,
    prompt_sha: str | None = None,
) -> JudgeRun:
    """Collapse one judge's replicated ratings into a sentinel JudgeRun.

    ``aggregate='modal'`` (default) matches judgekit's per-judge majority vote.
    ``aggregate='first'`` keeps the first replicate (single-pass view).
    """
    if aggregate not in AGGREGATES:
        raise ValueError(f"aggregate must be one of {sorted(AGGREGATES)}, got {aggregate!r}")
    if not judge_id:
        raise ValueError("judge_id is required")

    scores: dict[str, str] = {}
    missing_items: list[str] = []
    for item_id in sorted(panel.human_labels):
        per_judge = panel.ratings.get(item_id)
        if per_judge is None or judge_id not in per_judge:
            missing_items.append(item_id)
            continue
        reps = per_judge[judge_id]
        scores[item_id] = modal_label(reps) if aggregate == "modal" else str(reps[0])

    if missing_items:
        preview_n = 5
        preview = ", ".join(missing_items[:preview_n])
        more = (
            f" (+{len(missing_items) - preview_n} more)"
            if len(missing_items) > preview_n
            else ""
        )
        raise ValueError(
            f"judge {judge_id!r} has no ratings for human-labeled item(s): {preview}{more}"
        )
    if not scores:
        raise ValueError(f"no scores produced for judge {judge_id!r}")

    meta = panel.judges.get(judge_id, {})
    return JudgeRun(
        model=model if model is not None else str(meta.get("model") or judge_id),
        prompt_sha=prompt_sha if prompt_sha is not None else str(meta.get("prompt_sha", "")),
        anchor_scores=scores,
        live_metric=panel.live_metric,
        created=panel.created,
        source=panel.source,
    )


def write_anchors_jsonl(path: str | Path, anchors: AnchorSet) -> Path:
    """Write AnchorSet as sentinel JSONL (one {id, label} per line)."""
    out = Path(path)
    lines = [
        json.dumps({"id": i, "label": lab}, ensure_ascii=False)
        for i, lab in sorted(anchors.labels.items())
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def write_run_json(path: str | Path, run: JudgeRun) -> Path:
    """Write JudgeRun in the sentinel run JSON shape."""
    out = Path(path)
    payload: dict[str, Any] = {
        "judge": {"model": run.model, "prompt_sha": run.prompt_sha},
        "created": run.created,
        "anchor_scores": dict(run.anchor_scores),
    }
    if run.live_metric is not None:
        payload["live_metric"] = run.live_metric
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
