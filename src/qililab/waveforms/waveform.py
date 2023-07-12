from abc import abstractmethod
from typing import Protocol

from numpy import np


class Waveform(Protocol):
    duration: int
    resolution: int

    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
