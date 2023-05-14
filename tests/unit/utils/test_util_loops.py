""" Tests for utility methods for loops """


import numpy as np
import pytest

from qililab.typings import Parameter
from qililab.utils import Loop, util_loops


@pytest.fixture(name="loops")
def fixture_loops() -> list[Loop]:
    """Return Loop object with a loop inside aka nested loop"""
    loop1 = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))
    loop2 = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 32, 5))

    return [loop1, loop2]


@pytest.fixture(name="nested_loops")
def fixture_nested_loops() -> list[Loop]:
    """Return Loop object with a loop inside aka nested loop"""
    nested_loop1 = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))
    nested_loop1.loop = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 64, 6))

    nested_loop2 = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 32, 5))
    nested_loop2.loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 100, 100))

    return [nested_loop1, nested_loop2]


class TestUtilLoops:
    """Unit tests checking the Util Loop methods"""

    def test_compute_ranges_from_loops(self, loops: list[Loop] | None):
        """test computes ranges from a list of loops method"""
        expected = [np.geomspace(2, 32, 5), np.linspace(0, 10, 10)]
        for x, y in zip(util_loops.compute_ranges_from_loops(loops), expected):
            assert np.allclose(x, y)

    def test_compute_ranges_from_nested_loops(self, nested_loops: list[Loop] | None):
        """test compute ranges from a list of loops method with nested loops"""
        expected = [np.geomspace(2, 64, 6), np.geomspace(2, 32, 5), np.linspace(0, 100, 100), np.linspace(0, 10, 10)]
        for x, y in zip(util_loops.compute_ranges_from_loops(nested_loops), expected):
            assert np.allclose(x, y)

    @pytest.mark.parametrize("empty_loops", [None, []])
    def test_compute_ranges_from_empty_loops(self, empty_loops):
        """test compute ranges from a list of loops method with empty loops"""
        assert util_loops.compute_ranges_from_loops(empty_loops) == []

    def test_compute_shapes_from_loops(self, loops: list[Loop]):
        """test compute shapes from loops method"""
        assert util_loops.compute_shapes_from_loops(loops) == [5]

    def test_compute_shapes_from_nested_loops(self, nested_loops: list[Loop]):
        """test compute the shapes from loops method with nested loops"""
        assert util_loops.compute_shapes_from_loops(nested_loops) == [5, 6]

    @pytest.mark.parametrize("empty_loops", [None])
    def test_compute_shapes_from_empty_loops(self, empty_loops):
        """test compute the shapes from loops method with empty loops"""
        assert util_loops.compute_shapes_from_loops(empty_loops) == []
