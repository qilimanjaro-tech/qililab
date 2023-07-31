from abc import abstractmethod
from typing import Protocol

import numpy as np


class Waveform(Protocol):  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """
