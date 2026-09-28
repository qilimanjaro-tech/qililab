"""Unit tests for qililab.qprogram.loop_utils."""

import numpy as np
import pytest

from qililab.qprogram.loop_utils import calculate_iterations


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

    def test_count_exceeds_half_open_arange_by_the_endpoint(self):
        """`calculate_iterations` is endpoint-inclusive, whereas a half-open ``np.arange`` drops the
        endpoint. That one-point difference is the root cause of the StreamArray
        ``(40, 40, 2) -> (41, 41, 2)`` mismatch, so the two must not be used interchangeably."""
        start, stop, step = -0.21, 0.19, 0.01
        assert len(np.arange(start, stop, step)) == 40
        assert calculate_iterations(start, stop, step) == 41

    def test_zero_step_raises(self):
        with pytest.raises(ValueError, match="Step value cannot be zero"):
            calculate_iterations(0.0, 1.0, 0.0)

    def test_negative_count_for_malformed_range(self):
        # Step pointing away from stop -> non-positive count (callers clamp with max(..., 0)).
        assert calculate_iterations(0.0, 0.1, -0.01) <= 0
