import numpy as np
import pytest
from scipy.special import erf

from qililab.waveforms import FlatTop


@pytest.fixture(name="flat_top")
def fixture_flat_top():
    return FlatTop(amplitude=1, duration=10, gaussian=0.2, buffer=1)


class TestFlatTop:
    """Unit tests checking the FlatTop waveform attributes and methods."""
    def test_init(self, flat_top):
        """Test __init__ method"""
        assert flat_top.amplitude == 1
        assert flat_top.duration == 10
        assert flat_top.gaussian == 0.2
        assert flat_top.buffer == 1

    def test_envelope(self, flat_top):
        """Test envelope method"""

        # calculate envelope
        x = np.arange(0, flat_top.duration, 2)
        A = flat_top.amplitude
        g = flat_top.gaussian
        buf = flat_top.buffer
        dur = flat_top.duration
        envelope = 0.5 * A * np.real((erf(g * x - buf) - erf(g * (x - (dur + -buf / g)))))

        assert np.allclose(flat_top.envelope(resolution=2), envelope)

    def test_get_duration(self, flat_top):
        """Test that the duration is retrieved properly."""
        assert flat_top.get_duration() == flat_top.duration
