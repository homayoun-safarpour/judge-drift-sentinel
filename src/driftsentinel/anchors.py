"""The frozen anchor set: human-labeled examples the judge re-scores every run.

The anchor set is the instrument's reference weight. It must not move, so
`AnchorSet.freeze_hash` fingerprints the (id, input, label) records; if the hash in
your baseline no longer matches, someone edited the "frozen" set and every
longitudinal comparison built on it is void.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_MIN_DISTINCT_LABELS = 2


@dataclass(frozen=True)
class AnchorSet:
    """Human-labeled reference items. `labels` maps anchor id -> human label."""

    labels: dict[str, str]
    source: str = ""
    #: anchor id -> the anchor's `input` as read from the file (absent ids hash as null).
    inputs: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.labels:
            raise ValueError("anchor set is empty")

    @property
    def freeze_hash(self) -> str:
        """Stable fingerprint of the (id, input, label) records. Changes iff the set changes."""
        records = [[i, self.inputs.get(i), self.labels[i]] for i in sorted(self.labels)]
        canonical = json.dumps(records, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    def require_two_labels(self) -> None:
        """Refuse a set whose human labels are all the same.

        Cohen's kappa is undefined when every anchor carries one label: any
        imperfect judge scores 0.0, so a fall from 90% to 10% agreement would
        read as no drop at all.
        """
        distinct = sorted(set(self.labels.values()))
        if len(distinct) < _MIN_DISTINCT_LABELS:
            raise ValueError(
                f"anchor set has only one human label ({distinct[0]!r}); kappa is undefined, "
                "so judge drift cannot be measured. Add anchors with at least one other label."
            )

    def ids(self) -> set[str]:
        return set(self.labels)


def load_anchors(path: str | Path) -> AnchorSet:
    """Load an anchor set from JSONL: one {"id": ..., "label": ...} object per line."""
    labels: dict[str, str] = {}
    inputs: dict[str, Any] = {}
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        record = json.loads(line)
        for name in ("id", "label"):
            if name not in record:
                raise ValueError(f"{path} line {lineno}: missing required field '{name}'")
        anchor_id = str(record["id"])
        if anchor_id in labels:
            raise ValueError(f"{path} line {lineno}: duplicate anchor id '{anchor_id}'")
        labels[anchor_id] = str(record["label"])
        if "input" in record:
            inputs[anchor_id] = record["input"]
    return AnchorSet(labels=labels, source=str(path), inputs=inputs)
