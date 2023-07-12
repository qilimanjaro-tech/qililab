import numpy as np
import pytest

from qililab.waveforms import Arbitrary

samples = np.array(
    [
        0.64534116,
        0.61077185,
        0.84978029,
        0.71466369,
        0.65842367,
        0.77841013,
        0.85828779,
        0.20028723,
        0.45814018,
        0.45901151,
    ]
)


@pytest.fixture(name="arbitrary")
def fixture_square():
    return Arbitrary(samples=samples, resolution=0.1)


class TestArbitrary:
    def test_init(self, arbitrary):
        # test init method
        assert np.allclose(arbitrary.samples, samples)
        assert arbitrary.duration == 1
        assert arbitrary.resolution == 0.1

    def test_envelope(self, arbitrary):
        # test envelope method
        assert np.allclose(arbitrary.envelope(), samples)
