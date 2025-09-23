import numpy as np
import pytest

from qililab.waveforms import Gaussian, Square
from qililab.waveforms.gaussian_drag_correction import GaussianDragCorrection


@pytest.fixture(name="gaussian_drag_correction")
def fixture_gaussian_drag_correction():
    return GaussianDragCorrection(1.0, 100, 0.5, 2.5)


class TestGaussianDragCorrection:
    def test_init(self, gaussian_drag_correction: GaussianDragCorrection):
        # test init method
        assert gaussian_drag_correction.amplitude == 1.0
        assert gaussian_drag_correction.duration == 100
        assert gaussian_drag_correction.num_sigmas == 0.5
        assert gaussian_drag_correction.drag_coefficient == 2.5

    # def test_envelope_gaussian(self, gaussian_drag_correction: GaussianDragCorrection):
    #     # test envelope method
    #     sigma = gaussian_drag_correction.duration / gaussian_drag_correction.num_sigmas
    #     mu = gaussian_drag_correction.duration / 2
    #     x = np.arange(gaussian_drag_correction.duration)

    #     gaussian = Gaussian(amplitude=gaussian_drag_correction.amplitude, duration=gaussian_drag_correction.duration, num_sigmas=gaussian_drag_correction.num_sigmas)

    #     envelope = (-0.8 * (x - mu) / sigma**2) * gaussian.envelope()
    #     assert np.allclose(gaussian_drag_correction.envelope(), envelope)

    # def test_envelope_not_implemented_error(self):
    #     square = Square(amplitude=0.5, duration=100)
    #     drag_correction = GaussianDragCorrection(0.8, square)
    #     error_string = "Cannot apply drag correction on a Square waveform."
    #     with pytest.raises(NotImplementedError, match=error_string):
    #         drag_correction.envelope()
