from abc import abstractmethod
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class Waveform(Protocol):
    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
