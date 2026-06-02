import numpy as np
import pytest
from scipy.special import erf

from qililab.waveforms import FlatTop


@pytest.fixture(name="flat_top")
def fixture_flat_top():
    return FlatTop(amplitude=1, duration=30, smooth_duration=10, buffer=1)

@pytest.fixture(name="expected_envelope")
def fixture_envelope():
    return np.array([
        9.31423149e-04, 5.45474918e-03, 2.38574401e-02, 7.86496035e-02,
        1.98071955e-01, 3.88648705e-01, 6.11351295e-01, 8.01928045e-01,
        9.21350396e-01, 9.76142560e-01, 9.94545251e-01, 9.99068577e-01,
        9.99881983e-01, 9.99988953e-01, 9.99999201e-01, 9.99999201e-01,
        9.99988953e-01, 9.99881983e-01, 9.99068577e-01, 9.94545251e-01,
        9.76142560e-01, 9.21350396e-01, 8.01928045e-01, 6.11351295e-01,
        3.88648705e-01, 1.98071955e-01, 7.86496035e-02, 2.38574401e-02,
        5.45474918e-03, 9.31423149e-04
    ])


class TestFlatTop:
    """Unit tests checking the FlatTop waveform attributes and methods."""

    def test_init(self, flat_top):
        """Test __init__ method"""
        assert flat_top.amplitude == 1
        assert flat_top.duration == 30
        assert flat_top.smooth_duration == 10
        assert flat_top.buffer == 1

    def test_envelope(self, flat_top, expected_envelope):
        """Test envelope method"""
        env = flat_top.envelope()
        assert env.shape[0] == flat_top.duration
        assert np.allclose(env, expected_envelope)

    def test_get_duration(self, flat_top):
        """Test that the duration is retrieved properly."""
        assert flat_top.get_duration() == flat_top.duration
