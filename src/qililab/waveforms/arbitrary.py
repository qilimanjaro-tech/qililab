import numpy as np

from .waveform import Waveform


class Arbitrary(Waveform):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    def __init__(self, envelope: np.ndarray):
        self.samples = envelope

    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        return self.samples
