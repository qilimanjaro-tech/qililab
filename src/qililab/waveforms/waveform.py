from abc import abstractmethod
from typing import Protocol

import numpy as np


class Waveform(Protocol):
    duration: int
    resolution: int

    @abstractmethod
    def envelope(self):
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
