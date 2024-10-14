import numpy as np
import pytest

from qililab.waveforms import Arbitrary

samples = np.linspace(0, 100, 11)


@pytest.fixture(name="arbitrary")
def fixture_square():
    return Arbitrary(samples=samples)


class TestArbitrary:
    def test_init(self, arbitrary):
        # test init method
        assert np.allclose(arbitrary.samples, samples)

    def test_envelope(self, arbitrary):
        # test envelope method
        assert np.allclose(arbitrary.envelope(), samples)

    def test_envelope_with_higher_resolution(self, arbitrary):
        # test envelope method
        assert np.allclose(arbitrary.envelope(resolution=2), np.array([0.0, 20.0, 40.0, 60.0, 80.0, 100.0]))

    def test_get_duration_method(self, arbitrary):
        assert arbitrary.get_duration() == 11
