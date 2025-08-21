import numpy as np
import pytest
from scipy.special import erf

from qililab.waveforms import SquareSmooth


@pytest.fixture(name="square_smooth")
def fixture_square_smooth():
    return SquareSmooth(amplitude=1, duration=30, sigma=10, buffer=1)


class TestSquareSmooth:
    """Unit tests checking the SquareSmooth waveform attributes and methods."""

    def test_init(self, square_smooth):
        """Test __init__ method"""
        assert square_smooth.amplitude == 1
        assert square_smooth.duration == 30
        assert square_smooth.sigma == 10
        assert square_smooth.buffer == 1

    def test_envelope(self, square_smooth):
        """Test envelope method"""

        # calculate envelope
        x = np.arange(-square_smooth.duration / 2, square_smooth.duration / 2 + 1, 2)
        A = square_smooth.amplitude
        sigma = square_smooth.sigma
        buf = square_smooth.buffer
        dur = square_smooth.duration
        envelope = (
            0.5 * A * np.real((erf(4 * (x + (dur / 2 - buf)) / sigma - 2) - erf(4 * (x - (dur / 2 - buf)) / sigma + 2)))
        )

        assert np.allclose(square_smooth.envelope(resolution=2), envelope)

    def test_get_duration(self, square_smooth):
        """Test that the duration is retrieved properly."""
        assert square_smooth.get_duration() == square_smooth.duration
