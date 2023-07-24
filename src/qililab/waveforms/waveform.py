from abc import abstractmethod
from typing import Protocol

import numpy as np


class Waveform(Protocol):
    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
