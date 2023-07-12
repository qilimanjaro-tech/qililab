import numpy as np
import pytest

from qililab.waveforms import Square


@pytest.fixture(name="square")
def fixture_square():
    return Square(amplitude=0.5, duration=100, resolution=1)


class TestSquare:
    def test_init(self, square):
        # test init method
        assert square.amplitude == 0.5
        assert square.duration == 100
        assert square.resolution == 1

    def test_envelope(self, square):
        # test envelope method
        envelope = 0.5 * np.ones(round(100 / 1))
        assert np.allclose(square.envelope(), envelope)
