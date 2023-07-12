import numpy as np
import pytest

from qililab.waveforms import Gaussian


@pytest.fixture(name="gaussian")
def fixture_gaussian():
    return Gaussian(amplitude=1, duration=10, num_sigmas=2.5, resolution=2)


class TestGaussian:
    def test_init(self, gaussian):
        # test init method
        assert gaussian.amplitude == 1
        assert gaussian.duration == 10
        assert gaussian.resolution == 2
        assert gaussian.num_sigmas == 2.5

        assert gaussian.sigma == 4
        assert gaussian.mu == 5

    def test_envelope(self, gaussian):
        # test envelope method
        mu = 3
        sigma = 5
        # change values for mu and sigma and see if
        # envelope is what it should be
        gaussian.mu = mu
        gaussian.sigma = sigma

        # calculate envelope
        x = np.arange(5) * 2
        gaussian = np.exp(-0.5 * (x - mu) ** 2 / sigma**2)
        norm = np.amax(np.real(gaussian))
        gaussian = gaussian - gaussian[0]
        corr_norm = np.amax(np.real(gaussian))
        envelope = gaussian * norm / corr_norm

        assert np.allclose(gaussian.envelope, envelope)
