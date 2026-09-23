"""Unit tests for qililab.qprogram.loop_utils."""

import numpy as np
import pytest

from qililab.qprogram.loop_utils import calculate_iterations, loop_range


class TestCalculateIterations:
    @pytest.mark.parametrize(
        "start, stop, step, expected",
        [
            (0.0, 0.1, 0.01, 11),  # stop is inclusive
            (0, 10, 1, 11),
            (0.1, 0.0, -0.01, 11),  # descending
            (100, 200, 10, 11),
            (-0.21, 0.19, 0.01, 41),  # the flux-sweep case that previously mismatched
        ],
    )
    def test_counts_are_endpoint_inclusive(self, start, stop, step, expected):
        assert calculate_iterations(start, stop, step) == expected

    def test_zero_step_raises(self):
        with pytest.raises(ValueError, match="Step value cannot be zero"):
            calculate_iterations(0.0, 1.0, 0.0)


class TestLoopRange:
    def test_length_matches_calculate_iterations(self):
        start, stop, step = -0.21, 0.19, 0.01
        values = loop_range(start, stop, step)
        assert len(values) == calculate_iterations(start, stop, step)

    def test_includes_endpoint_unlike_arange(self):
        """np.arange is half-open and drops the endpoint; loop_range keeps it. This one-point
        difference is the root cause of the StreamArray `(40, 40, 2) -> (41, 41, 2)` mismatch."""
        start, stop, step = -0.21, 0.19, 0.01
        assert len(np.arange(start, stop, step)) == 40
        values = loop_range(start, stop, step)
        assert len(values) == 41
        np.testing.assert_allclose(values[-1], stop)

    def test_matches_arange_when_arange_is_already_inclusive(self):
        # A range whose endpoint arange happens to include: values must agree.
        values = loop_range(0.0, 0.1, 0.01)
        np.testing.assert_allclose(values, np.linspace(0.0, 0.1, 11))

    def test_empty_for_malformed_range(self):
        # Step pointing away from stop -> no iterations, empty array (does not raise).
        assert loop_range(0.0, 0.1, -0.01).size == 0
