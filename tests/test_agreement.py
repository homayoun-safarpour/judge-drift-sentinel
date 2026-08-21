import pytest

from driftsentinel.agreement import (
    agreement_kappa,
    cohen_kappa,
    flip_rate,
    observed_agreement,
    weighted_cohen_kappa,
)


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


def test_weighted_kappa_perfect_ordinal_agreement_is_one():
    labels = {"a": "0", "b": "1", "c": "2", "d": "3"}
    assert weighted_cohen_kappa(labels, dict(labels), weights="linear") == pytest.approx(1.0)
    assert weighted_cohen_kappa(labels, dict(labels), weights="quadratic") == pytest.approx(1.0)


def test_weighted_kappa_rejects_non_integer_labels():
    with pytest.raises(ValueError, match="integer labels"):
        weighted_cohen_kappa({"a": "pass"}, {"a": "fail"}, weights="linear")


def test_weighted_kappa_hand_computed_linear_on_0_3():
    # 4 items on scale 0-3. human: 0,1,2,3  judge: 0,2,2,3
    # Linear weights: |d|=0 -> 1, |d|=1 -> 2/3, |d|=2 -> 1/3, |d|=3 -> 0
    # po = (1 + 2/3 + 1 + 1) / 4 = 11/12
    # Hand pe over uniform row marg and col [0.25,0,0.5,0.25] yields 7/12;
    # kappa = (11/12 - 7/12) / (1 - 7/12) = 0.8
    human = {"a": "0", "b": "1", "c": "2", "d": "3"}
    judge = {"a": "0", "b": "2", "c": "2", "d": "3"}
    assert weighted_cohen_kappa(
        human, judge, weights="linear", levels=(0, 1, 2, 3)
    ) == pytest.approx(0.8)


def test_weighted_kappa_separates_near_miss_from_far_miss_on_ordinal_scale():
    # Central claim: on a 0-3 rubric, off-by-1 disagreements must score higher
    # weighted kappa than off-by-3 disagreements on the same items. Unweighted
    # kappa treats both as total misses and cannot separate them.
    human = {
        "a": "0",
        "b": "0",
        "c": "1",
        "d": "0",
        "e": "2",
        "f": "3",
        "g": "3",
        "h": "3",
    }
    near = {
        "a": "0",
        "b": "1",
        "c": "1",
        "d": "1",
        "e": "2",
        "f": "2",
        "g": "3",
        "h": "2",
    }
    far = {
        "a": "0",
        "b": "3",
        "c": "1",
        "d": "3",
        "e": "2",
        "f": "0",
        "g": "3",
        "h": "0",
    }
    levels = (0, 1, 2, 3)
    # Same disagreeing ids -> same raw agreement; unweighted kappa ignores distance.
    assert observed_agreement(human, near) == pytest.approx(observed_agreement(human, far))
    near_k = weighted_cohen_kappa(human, near, weights="linear", levels=levels)
    far_k = weighted_cohen_kappa(human, far, weights="linear", levels=levels)
    assert near_k > far_k
    near_q = weighted_cohen_kappa(human, near, weights="quadratic", levels=levels)
    far_q = weighted_cohen_kappa(human, far, weights="quadratic", levels=levels)
    assert near_q > far_q


def test_quadratic_penalizes_far_misses_more_than_linear():
    # Named claim: on the same ordinal near/far pair, quadratic weights
    # (Fleiss-Cohen) open a larger near-minus-far gap than linear
    # (Cicchetti-Allison). Near misses get more credit under quadratic;
    # far misses score lower, so the separation is sharper.
    human = {
        "a": "0",
        "b": "0",
        "c": "1",
        "d": "0",
        "e": "2",
        "f": "3",
        "g": "3",
        "h": "3",
    }
    near = {
        "a": "0",
        "b": "1",
        "c": "1",
        "d": "1",
        "e": "2",
        "f": "2",
        "g": "3",
        "h": "2",
    }
    far = {
        "a": "0",
        "b": "3",
        "c": "1",
        "d": "3",
        "e": "2",
        "f": "0",
        "g": "3",
        "h": "0",
    }
    levels = (0, 1, 2, 3)
    near_linear = weighted_cohen_kappa(human, near, weights="linear", levels=levels)
    far_linear = weighted_cohen_kappa(human, far, weights="linear", levels=levels)
    near_quad = weighted_cohen_kappa(human, near, weights="quadratic", levels=levels)
    far_quad = weighted_cohen_kappa(human, far, weights="quadratic", levels=levels)
    assert near_quad > near_linear
    assert far_quad < far_linear
    assert (near_quad - far_quad) > (near_linear - far_linear)


def test_agreement_kappa_none_keeps_binary_path():
    a = {"1": "pass", "2": "pass", "3": "fail", "4": "fail"}
    b = {"1": "pass", "2": "fail", "3": "pass", "4": "fail"}
    assert agreement_kappa(a, b, weights="none") == pytest.approx(cohen_kappa(a, b))


def test_agreement_kappa_linear_matches_weighted():
    human = {"a": "0", "b": "1", "c": "2", "d": "3"}
    judge = {"a": "0", "b": "2", "c": "2", "d": "3"}
    levels = (0, 1, 2, 3)
    assert agreement_kappa(human, judge, weights="linear", levels=levels) == pytest.approx(
        weighted_cohen_kappa(human, judge, weights="linear", levels=levels)
    )
