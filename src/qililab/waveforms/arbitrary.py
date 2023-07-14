import numpy as np

from qililab.config import logger

from .waveform import Waveform


class Arbitrary(Waveform):
    def __init__(self, samples: np.ndarray, duration: int | None = None):
        self.samples = samples
        self.duration = len(samples) if duration is None else duration

    def envelope(self, resolution: float = 1) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
        if len(self.samples) != self.duration / resolution:
            raise ValueError(
                f"Duration / resolution does not correspond to len(samples): {self.duration} / {resolution} != {len(self.samples)}"
            )
        return self.samples
