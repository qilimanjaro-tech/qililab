import numpy as np
import pytest

from qililab.waveforms import Gaussian, Square
from qililab.waveforms.drag_correction import DragCorrection


@pytest.fixture(name="gaussian")
def fixture_gaussian():
    return Gaussian(amplitude=1, duration=10, num_sigmas=2.5, resolution=2)


class TestDragCorrection:
    def test_init(self, gaussian):
        # test init method
        drag_correction = DragCorrection(0.8, gaussian)
        assert drag_correction.drag_coefficient == 0.8
        assert isinstance(drag_correction.waveform, Gaussian)

    def test_envelope_gaussian(self, gaussian):
        # test envelope method

        drag_correction = DragCorrection(0.8, gaussian)
        x = np.arange(gaussian.duration / gaussian.resolution) * gaussian.resolution
        envelope = (-0.8 * (x - gaussian.mu) / gaussian.sigma**2) * gaussian.envelope()
        assert np.allclose(drag_correction.envelope(), envelope)

    def test_envelope_not_implemented_error(self):
        square = Square(amplitude=0.5, duration=100, resolution=1)
        drag_correction = DragCorrection(0.8, square)
        with pytest.raises(NotImplementedError):
            drag_correction.envelope
