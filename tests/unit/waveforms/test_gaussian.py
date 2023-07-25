import numpy as np
import pytest

from qililab.waveforms import Gaussian


@pytest.fixture(name="gaussian")
def fixture_gaussian():
    return Gaussian(amplitude=1, duration=10, num_sigmas=2.5)


class TestGaussian:
    def test_init(self, gaussian):
        # test init method
        assert gaussian.amplitude == 1
        assert gaussian.duration == 10
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
        envelope = np.exp(-0.5 * (x - mu) ** 2 / sigma**2)
        norm = np.amax(np.real(envelope))
        envelope = envelope - envelope[0]
        corr_norm = np.amax(np.real(envelope))
        envelope = envelope * norm / corr_norm

        assert np.allclose(gaussian.envelope(resolution=2), envelope)

    def test_amplitude_0(self, gaussian):
        gaussian.amplitude = 0
        assert np.allclose(gaussian.envelope(), np.zeros(10))
