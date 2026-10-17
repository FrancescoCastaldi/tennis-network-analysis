import numpy as np
import pytest

from tennis_networks import hypotheses as hy
from tennis_networks import tennisdata as td


def test_permutation_test_finds_no_difference_between_identical_groups(matches):
    m = td.played(matches)
    res = hy.permutation_test(m, m, len, n_perm=50, seed=1)
    assert res["diff"] == 0
    assert res["p_value"] == pytest.approx(1.0)


def test_signflip_test_on_constant_positive_differences():
    res = hy.paired_signflip_test(np.ones(12), n_perm=2000, seed=1)
    assert res["mean_diff"] == 1
    assert res["p_value"] < 0.01


def test_group_permutation_test_separates_distinct_groups():
    res = hy.group_permutation_test(np.arange(10) + 100, np.arange(10), n_perm=999, seed=1)
    assert res["p_value"] < 0.01
