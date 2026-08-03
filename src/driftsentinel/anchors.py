"""The frozen anchor set: human-labeled examples the judge re-scores every run.

The anchor set is the instrument's reference weight. It must not move, so
`AnchorSet.freeze_hash` fingerprints the (id, label) pairs; if the hash in
your baseline no longer matches, someone edited the "frozen" set and every
longitudinal comparison built on it is void.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnchorSet:
    """Human-labeled reference items. `labels` maps anchor id -> human label."""

    labels: dict[str, str]
    source: str = ""

    def __post_init__(self) -> None:
        if not self.labels:
            raise ValueError("anchor set is empty")

    @property
    def freeze_hash(self) -> str:
        """Stable fingerprint of the (id, label) pairs. Changes iff the set changes."""
        canonical = json.dumps(sorted(self.labels.items()))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    def ids(self) -> set[str]:
        return set(self.labels)


def load_anchors(path: str | Path) -> AnchorSet:
    """Load an anchor set from JSONL: one {"id": ..., "label": ...} object per line."""
    labels: dict[str, str] = {}
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        record = json.loads(line)
        for field in ("id", "label"):
            if field not in record:
                raise ValueError(f"{path} line {lineno}: missing required field '{field}'")
        anchor_id = str(record["id"])
        if anchor_id in labels:
            raise ValueError(f"{path} line {lineno}: duplicate anchor id '{anchor_id}'")
        labels[anchor_id] = str(record["label"])
    return AnchorSet(labels=labels, source=str(path))
