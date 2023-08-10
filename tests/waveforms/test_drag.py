import numpy as np

from qililab.waveforms import DragWaveform, Gaussian
from qililab.waveforms.drag_correction import DragCorrection


class TestDrag:
    def test_init(self):
        # test init method
        drag = DragWaveform(drag_coefficient=0.4, amplitude=0.7, duration=40, num_sigmas=2)
        gaus = Gaussian(amplitude=0.7, duration=40, num_sigmas=2)
        corr = DragCorrection(drag_coefficient=0.4, waveform=gaus)

        assert isinstance(drag.I, Gaussian)
        assert isinstance(drag.Q, DragCorrection)
        assert np.allclose(drag.I.envelope(), gaus.envelope())
        assert np.allclose(drag.Q.envelope(), corr.envelope())
