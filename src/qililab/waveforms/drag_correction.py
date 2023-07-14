import numpy as np

from .gaussian import Gaussian
from .waveform import Waveform


class DragCorrection(Waveform):
    """Calculates the first order drag correction of the imaginary (Ey) channel of a drive pulse. See https://arxiv.org/abs/0901.0534 (10).
    So far only implemented for Gaussian pulses
    """

    def __init__(self, drag_coefficient: float, waveform: Waveform):
        """Init method

        Args:
            drag_coefficient (float): drag coefficient
            waveform (Waveform): waveform on which the drag transformation is calculated
        """
        self.drag_coefficient = drag_coefficient
        self.waveform = waveform
        self.duration = waveform.duration

    def envelope(self, resolution: float = 1):
        """Returns the envelope corresponding to the drag correction

        Returns:
            np.ndarray
        """
        if isinstance(self.waveform, Gaussian):
            x = np.arange(self.waveform.duration / resolution) * resolution

            return (
                -1 * self.drag_coefficient * (x - self.waveform.mu) / self.waveform.sigma**2
            ) * self.waveform.envelope()
        else:
            raise NotImplementedError
