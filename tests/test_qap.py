import numpy as np
import pytest

from tennis_networks.qap import collinearity_diagnostics, permutation_regression, qap_correlation


def _random_matrix(n, seed):
    m = np.random.default_rng(seed).random((n, n))
    np.fill_diagonal(m, 0)
    return m


def test_qap_detects_identical_matrices():
    m = _random_matrix(30, 1)
    res = qap_correlation(m, m, n_perm=199, seed=1)
    assert res["r"] == pytest.approx(1.0)
    assert res["p_value"] == pytest.approx(1 / 200)


def test_qap_does_not_reject_independent_matrices():
    res = qap_correlation(_random_matrix(30, 1), _random_matrix(30, 2), n_perm=199, seed=1)
    assert abs(res["r"]) < 0.1
    assert res["p_value"] > 0.05


def test_qap_rejects_non_square_input():
    with pytest.raises(ValueError):
        qap_correlation(np.zeros((3, 4)), np.zeros((3, 4)))


def test_permutation_regression_finds_the_true_predictor():
    rng = np.random.default_rng(0)
    x = rng.normal(size=(200, 2))
    y = 2 * x[:, 0] + rng.normal(scale=0.5, size=200)
    rows = permutation_regression(y, x, ["signal", "noise"], n_perm=199, seed=1)
    by_name = {r["predictor"]: r for r in rows}
    assert by_name["signal"]["p_value"] < 0.01
    assert by_name["noise"]["p_value"] > 0.05
    assert by_name["signal"]["r2"] > 0.8


def test_collinearity_diagnostics_exposes_predictor_dependence():
    x = np.column_stack([np.arange(10), np.arange(10) * 2])
    res = collinearity_diagnostics(x, ["pagerank", "wins"])
    assert res["max_abs_correlation"] == pytest.approx(1.0)
    assert res["condition_number"] > 1e10
