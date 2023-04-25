""" Tests for utility methods for loops """
from typing import List

import numpy as np
import pytest

from qililab.typings import Parameter
from qililab.utils import Loop, util_loops


@pytest.fixture(name="loops")
def fixture_loops() -> List[Loop]:
    """Return Loop object with a loop inside aka nested loop"""
    loop1 = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))
    loop2 = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 32, 5))

    return [loop1, loop2]


@pytest.fixture(name="nested_loops")
def fixture_nested_loops() -> List[Loop]:
    """Return Loop object with a loop inside aka nested loop"""
    nested_loop1 = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))
    nested_loop1.loop = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 64, 6))

    nested_loop2 = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 32, 5))
    nested_loop2.loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 100, 100))

    return [nested_loop1, nested_loop2]


class TestUtilLoops:
    """Unit tests checking the Util Loop methods"""

    def test_find_minimum_outer_range_from_loops(self, loops: List[Loop]):
        """test find minimum outer range method from same level loops"""
        expected = np.geomspace(2, 32, 5)
        np.testing.assert_array_equal(util_loops.find_minimum_outer_range_from_loops(loops), expected)

    @pytest.mark.xfail(reason="[BUG] Reported in Issue #265")
    def test_find_minimum_outer_range_from_nested_loops(self, nested_loops: List[Loop]):
        """test find minimum outer range method from same level with nested loops"""
        expected = np.geomspace(2, 32, 5)
        np.testing.assert_array_equal(util_loops.find_minimum_outer_range_from_loops(nested_loops), expected)

    @pytest.mark.parametrize("empty_loops", [None, []])
    def test_find_minimum_outer_range_from_empty_loops(self, empty_loops):
        """test find minimum outer range method from same level with empty loops"""
        expected = np.array([], dtype=object)
        np.testing.assert_array_equal(util_loops.find_minimum_outer_range_from_loops(empty_loops), expected)

    def test_find_minimum_inner_range_from_loops(self, loops: List[Loop]):
        """test find minimum inner range method from same level loops"""
        expected = np.array([], dtype=object)
        np.testing.assert_array_equal(util_loops.find_minimum_inner_range_from_loops(loops), expected)

    @pytest.mark.xfail(reason="[BUG] Reported in Issue #265")
    def test_find_minimum_inner_range_from_nested_loops(self, nested_loops: List[Loop]):
        """test find minimum inner range method from same level with nested loops"""
        expected = np.geomspace(2, 64, 6)
        np.testing.assert_array_equal(util_loops.find_minimum_inner_range_from_loops(nested_loops), expected)

    @pytest.mark.parametrize("empty_loops", [None, []])
    def test_find_minimum_inner_range_from_empty_loops(self, empty_loops):
        """test find minimum inner range method from same level with empty loops"""
        expected = np.array([], dtype=object)
        np.testing.assert_array_equal(util_loops.find_minimum_inner_range_from_loops(empty_loops), expected)

    def test_find_minimum_range_from_loops(self, loops: List[Loop]):
        """test find minimum range method from same level loops"""
        expected = np.geomspace(2, 32, 5)
        np.testing.assert_array_equal(util_loops._find_minimum_range_from_loops(loops), expected)

    @pytest.mark.parametrize("empty_loops", [None, []])
    def test_find_minimum_range_from_empty_loops(self, empty_loops):
        """test find minimum inner range method from same level with empty loops"""
        expected = np.array([], dtype=object)
        np.testing.assert_array_equal(util_loops._find_minimum_range_from_loops(empty_loops), expected)

    def test_create_loops_from_inner_loops(self, nested_loops):
        """test create loops from inner loops method with nested loops"""
        expected_loop1 = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 64, 6))
        expected_loop2 = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 100, 100))
        expected = [expected_loop1, expected_loop2]
        for x, y in zip(util_loops._create_loops_from_inner_loops(nested_loops), expected):
            assert x.alias == y.alias
            assert x.parameter == y.parameter
            np.testing.assert_array_equal(x.values, y.values)

    def test_compute_ranges_from_loops(self, loops: List[Loop] | None):
        """test computes ranges from a list of loops method"""
        expected = [np.geomspace(2, 32, 5), np.linspace(0, 10, 10)]
        for x, y in zip(util_loops.compute_ranges_from_loops(loops), expected):
            np.testing.assert_array_equal(x, y)

    def test_compute_ranges_from_nested_loops(self, nested_loops: List[Loop] | None):
        """test compute ranges from a list of loops method with nested loops"""
        expected = [np.geomspace(2, 64, 6), np.geomspace(2, 32, 5), np.linspace(0, 100, 100), np.linspace(0, 10, 10)]
        for x, y in zip(util_loops.compute_ranges_from_loops(nested_loops), expected):
            np.testing.assert_array_equal(x, y)

    @pytest.mark.parametrize("empty_loops", [None, []])
    def test_compute_ranges_from_empty_loops(self, empty_loops):
        """test compute ranges from a list of loops method with empty loops"""
        assert util_loops.compute_ranges_from_loops(empty_loops) == []

    def test_compute_shapes_from_loops(self, loops: List[Loop]):
        """test compute shapes from loops method"""
        expected = [5]
        assert util_loops.compute_shapes_from_loops(loops) == expected

    def test_compute_shapes_from_nested_loops(self, nested_loops: List[Loop]):
        """test compute the shapes from loops method with nested loops"""
        expected = [5, 6]
        assert util_loops.compute_shapes_from_loops(nested_loops) == expected

    @pytest.mark.parametrize("empty_loops", [None])
    def test_compute_shapes_from_empty_loops(self, empty_loops):
        """test compute the shapes from loops method with empty loops"""
        assert util_loops.compute_shapes_from_loops(empty_loops) == []
