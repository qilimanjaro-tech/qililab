import numpy as np
import pytest

from qililab.waveforms import Gaussian, Square
from qililab.waveforms.drag_correction import DragCorrection


@pytest.fixture(name="gaussian")
def fixture_gaussian():
    return Gaussian(amplitude=1, duration=10, num_sigmas=2.5)


class TestDragCorrection:
    def test_init(self, gaussian):
        # test init method
        drag_correction = DragCorrection(0.8, gaussian)
        assert drag_correction.drag_coefficient == 0.8
        assert isinstance(drag_correction.waveform, Gaussian)

    def test_envelope_gaussian(self, gaussian):
        # test envelope method

        drag_correction = DragCorrection(0.8, gaussian)
        sigma = gaussian.duration / gaussian.num_sigmas
        mu = gaussian.duration / 2
        x = np.arange(gaussian.duration)
        envelope = (-0.8 * (x - mu) / sigma**2) * gaussian.envelope()
        assert np.allclose(drag_correction.envelope(), envelope)

    def test_envelope_not_implemented_error(self):
        square = Square(amplitude=0.5, duration=100)
        drag_correction = DragCorrection(0.8, square)
        error_string = "Cannot apply drag correction on a Square waveform."
        with pytest.raises(NotImplementedError, match=error_string):
            drag_correction.envelope()
