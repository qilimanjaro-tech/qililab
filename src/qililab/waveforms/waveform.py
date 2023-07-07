from abc import ABC, abstractmethod

from numpy import np


class Waveform(ABC):
    duration: int
    resolution: int

    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
