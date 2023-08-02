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

    def envelope(self, resolution: float = 1):
        """Returns the envelope corresponding to the drag correction

        Args:
            resolution (int, optional): Pulse resolution. Defaults to 1.

        Returns:
            np.ndarray
        """
        if isinstance(self.waveform, Gaussian):
            sigma = self.waveform.duration / self.waveform.num_sigmas
            mu = self.waveform.duration / 2
            x = np.arange(self.waveform.duration / resolution) * resolution

            return (-1 * self.drag_coefficient * (x - mu) / sigma**2) * self.waveform.envelope()
        else:
            raise NotImplementedError(f"Cannot apply drag correction on a {self.waveform.__class__.__name__} waveform.")
