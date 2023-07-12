import numpy as np

from .waveform import Waveform


class Arbitrary(Waveform):
    def __init__(self, samples: np.ndarray, resolution: int = 1):
        self.samples = samples
        self.duration = len(samples) * resolution
        self.resolution = resolution

    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        return self.samples
