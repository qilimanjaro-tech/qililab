import numpy as np
import pytest

from qililab.waveforms import Square


@pytest.fixture(name="square")
def fixture_square():
    return Square(amplitude=0.5, duration=100)


class TestSquare:
    def test_init(self, square):
        """Test __init__ method"""
        assert square.amplitude == 0.5
        assert square.duration == 100

    def test_envelope_method(self, square):
        """Test envelope method"""
        envelope = 0.5 * np.ones(round(100 / 1))
        assert np.allclose(square.envelope(), envelope)

    def test_get_duration_method(self, square):
        """Test get_duration method"""
        assert square.get_duration() == 100
