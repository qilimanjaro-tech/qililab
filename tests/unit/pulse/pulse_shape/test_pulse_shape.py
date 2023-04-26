"""Tests for the PulseShape class."""
import numpy as np
import pytest

from qililab.pulse.pulse_shape import Drag, Gaussian, PulseShape, Rectangular


@pytest.fixture(
    name="pulse_shape", params=[Rectangular(), Gaussian(num_sigmas=4), Drag(num_sigmas=4, drag_coefficient=1.0)]
)
def fixture_pulse_shape(request: pytest.FixtureRequest) -> PulseShape:
    """Return Rectangular object."""
    return request.param  # type: ignore


class TestPulseShape:
    """Unit tests checking the PulseShape attributes and methods"""

    def test_envelope_method(self, pulse_shape: PulseShape):
        """Test envelope method"""
        envelope = pulse_shape.envelope(duration=50, amplitude=2.0, resolution=0.1)
        assert isinstance(envelope, np.ndarray)

    def test_to_dict_method(self, pulse_shape: PulseShape):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()
        assert isinstance(dictionary, dict)
