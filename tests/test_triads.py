import math

import networkx as nx
import pytest

from tennis_networks.triads import cyclic_ratio


def test_transitive_triangle_has_no_cycles():
    g = nx.DiGraph([("c", "b"), ("b", "a"), ("c", "a")])  # loser -> winner: a beats both
    assert cyclic_ratio(g) == 0


def test_cycles_and_transitive_triangles_are_counted():
    g = nx.DiGraph([("c", "b"), ("b", "a"), ("c", "a")])
    g.add_edges_from([("x", "y"), ("y", "z"), ("z", "x")])
    g.add_edges_from([("p", "q"), ("q", "r"), ("p", "r")])
    assert cyclic_ratio(g) == pytest.approx(0.5)


def test_ratio_is_undefined_without_transitive_triads():
    assert math.isnan(cyclic_ratio(nx.DiGraph([("x", "y"), ("y", "z"), ("z", "x")])))
