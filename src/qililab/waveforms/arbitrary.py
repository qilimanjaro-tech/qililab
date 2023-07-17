import numpy as np

from qililab.config import logger

from .waveform import Waveform


class Arbitrary(Waveform):
    def __init__(self, envelope: np.ndarray):
        self.samples = envelope

    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        return self.samples
