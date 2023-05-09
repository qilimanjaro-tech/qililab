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
        envelope = pulse_shape.envelope(duration=50, amplitude=1.0, resolution=0.1)
        envelope2 = pulse_shape.envelope(duration=50, amplitude=1.0)
        envelope3 = pulse_shape.envelope(duration=500, amplitude=2.0)

        for env in [envelope, envelope2, envelope3]:
            assert env is not None
            assert isinstance(env, np.ndarray)

        assert round(np.max(np.abs(envelope)), 15) == 1.0
        assert round(np.max(np.abs(envelope2)), 15) == 1.0
        assert round(np.max(np.abs(envelope3)), 15) == 2.0
        assert len(envelope) == len(envelope2) * 10 == len(envelope3)

    def test_to_dict_method(self, pulse_shape: PulseShape):
        """Test to_dict method"""
        dictionary = pulse_shape.to_dict()
        assert dictionary is not None
        assert isinstance(dictionary, dict)
