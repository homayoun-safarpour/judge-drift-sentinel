import pytest

from driftsentinel.agreement import cohen_kappa, flip_rate, observed_agreement


def test_kappa_perfect_agreement_is_one():
    labels = {"a": "pass", "b": "fail", "c": "pass"}
    assert cohen_kappa(labels, dict(labels)) == pytest.approx(1.0)


def test_kappa_chance_level_agreement_is_zero():
    # Observed agreement 0.5 with 50/50 marginals on both sides:
    # expected chance agreement is also 0.5, so kappa must be exactly 0.
    a = {"1": "pass", "2": "pass", "3": "fail", "4": "fail"}
    b = {"1": "pass", "2": "fail", "3": "pass", "4": "fail"}
    assert cohen_kappa(a, b) == pytest.approx(0.0)


def test_kappa_matches_hand_computed_value():
    # 10 items, 8 agreements, marginals 6/4 both sides:
    # po = 0.8, pe = 0.6*0.6 + 0.4*0.4 = 0.52, kappa = 0.28/0.48 = 7/12.
    a = {str(i): "pass" for i in range(1, 7)} | {str(i): "fail" for i in range(7, 11)}
    b = dict(a)
    b["6"] = "fail"
    b["7"] = "pass"
    assert cohen_kappa(a, b) == pytest.approx(7 / 12)


def test_kappa_single_label_degenerate_case_is_defined():
    same = {"a": "pass", "b": "pass"}
    assert cohen_kappa(same, dict(same)) == pytest.approx(1.0)


def test_kappa_compares_only_shared_ids():
    a = {"a": "pass", "b": "fail", "only_in_a": "pass"}
    b = {"a": "pass", "b": "fail", "only_in_b": "fail"}
    assert observed_agreement(a, b) == pytest.approx(1.0)


def test_no_shared_ids_raises():
    with pytest.raises(ValueError, match="no shared item ids"):
        cohen_kappa({"a": "pass"}, {"b": "pass"})


def test_flip_rate_counts_changed_labels():
    a = {"1": "pass", "2": "pass", "3": "fail", "4": "fail"}
    b = {"1": "pass", "2": "fail", "3": "fail", "4": "pass"}
    assert flip_rate(a, b) == pytest.approx(0.5)
