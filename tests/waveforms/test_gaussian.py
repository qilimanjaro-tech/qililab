import numpy as np
import pytest

from qililab.waveforms import Gaussian


@pytest.fixture(name="gaussian")
def fixture_gaussian():
    return Gaussian(amplitude=1, duration=10, num_sigmas=2.5)


class TestGaussian:
    def test_init(self, gaussian):
        """Test __init__ method"""
        assert gaussian.amplitude == 1
        assert gaussian.duration == 10
        assert gaussian.num_sigmas == 2.5

    def test_envelope(self, gaussian):
        """Test envelope method"""

        # calculate envelope
        sigma = gaussian.duration / gaussian.num_sigmas
        mu = gaussian.duration / 2
        x = np.arange(5) * 2
        envelope = np.exp(-0.5 * (x - mu) ** 2 / sigma**2)
        norm = np.amax(np.real(envelope))
        envelope = envelope - envelope[0]
        corr_norm = np.amax(np.real(envelope))
        envelope = envelope * norm / corr_norm

        assert np.allclose(gaussian.envelope(resolution=2), envelope)

    def test_envelope_method_with_zero_amplitude(self, gaussian):
        """Test envelope method when amplitude is zero."""
        gaussian.amplitude = 0
        assert np.allclose(gaussian.envelope(), np.zeros(10))
