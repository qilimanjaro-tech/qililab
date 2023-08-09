"""Tests for the Loop class."""
import numpy as np
import pytest

from qililab.typings import Parameter
from qililab.utils import Loop


@pytest.fixture(name="loop")
def fixture_loop() -> Loop:
    """Return Loop object"""
    return Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))


@pytest.fixture(name="nested_loop")
def fixture_nested_loop() -> Loop:
    """Return Loop object with a loop inside aka nested loop"""
    nested_loop = Loop(alias="X", parameter=Parameter.AMPLITUDE, values=np.linspace(0, 10, 10))
    nested_loop.loop = Loop(alias="Y", parameter=Parameter.AMPLITUDE, values=np.geomspace(2, 32, 5))
    return nested_loop


class TestLoop:
    """Unit tests checking the Loop attributes and methods"""

    def test_num_loops_property(self, loop: Loop):
        """Test num_loops property."""
        assert loop.num_loops == 1

    def test_num_loops_property_nested_loop(self, nested_loop: Loop):
        """Test num_loops property for a nested loop."""
        assert nested_loop.num_loops == 2

    def test_ranges_property(self, loop: Loop):
        """Terst the ranges property"""
        expected = np.array([np.linspace(0, 10, 10)], dtype=object)
        np.testing.assert_array_equal(loop.all_values, expected)

    def test_ranges_property_nested_loop(self, nested_loop: Loop):
        """Terst the ranges property for a nested loop"""
        range_1 = np.linspace(0, 10, 10)
        range_2 = np.geomspace(2, 32, 5)
        expected = np.array([range_1, range_2], dtype=object)
        for x, y in zip(nested_loop.all_values, expected):
            np.testing.assert_array_equal(x, y)

    def test_shapes_property(self, loop: Loop):
        """Test the shapes property"""
        assert loop.shape == [10]

    def test_shapes_property_nested_loop(self, nested_loop: Loop):
        """Test the shapes property for a nested loop"""
        assert nested_loop.shape == [10, 5]

    def test_loops_property(self, loop: Loop):
        """Test the loops property"""
        assert all(isinstance(x, Loop) for x in loop.loops)
        assert len(loop.loops) == 1

    def test_loops_property_nested_loop(self, nested_loop: Loop):
        """Test the loops property for a nested loop"""
        assert all(isinstance(x, Loop) for x in nested_loop.loops)
        assert len(nested_loop.loops) == 2

    def test_start_property(self, loop: Loop):
        """ "Test the start property"""
        assert loop.start == 0.0

    def test_stop_property(self, loop: Loop):
        """ "Test the stop property"""
        assert loop.stop == 10.0

    def test_num_property(self, loop: Loop):
        """ "Test the num property"""
        assert loop.num == 10
