import pytest

from driftsentinel.anchors import AnchorSet, load_anchors


def write_jsonl(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_load_anchors_reads_ids_and_labels(tmp_path):
    path = write_jsonl(
        tmp_path / "anchors.jsonl",
        ['{"id": "a1", "label": "pass"}', '{"id": "a2", "label": "fail", "input": "extra ok"}'],
    )
    anchors = load_anchors(path)
    assert anchors.labels == {"a1": "pass", "a2": "fail"}


def test_duplicate_anchor_ids_are_rejected(tmp_path):
    path = write_jsonl(
        tmp_path / "anchors.jsonl",
        ['{"id": "a1", "label": "pass"}', '{"id": "a1", "label": "fail"}'],
    )
    with pytest.raises(ValueError, match="duplicate anchor id"):
        load_anchors(path)


def test_missing_label_field_is_rejected(tmp_path):
    path = write_jsonl(tmp_path / "anchors.jsonl", ['{"id": "a1"}'])
    with pytest.raises(ValueError, match="missing required field 'label'"):
        load_anchors(path)


def test_empty_anchor_set_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        AnchorSet(labels={})


def test_freeze_hash_changes_when_a_label_changes():
    original = AnchorSet(labels={"a1": "pass", "a2": "fail"})
    edited = AnchorSet(labels={"a1": "pass", "a2": "pass"})
    assert original.freeze_hash != edited.freeze_hash


def test_freeze_hash_is_order_independent():
    one = AnchorSet(labels={"a1": "pass", "a2": "fail"})
    two = AnchorSet(labels={"a2": "fail", "a1": "pass"})
    assert one.freeze_hash == two.freeze_hash
