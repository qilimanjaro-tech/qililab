from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


class Waveform(ABC):
    duration: int
    resolution: int

    @abstractmethod
    def envelope(self) -> np.ndarray:
        """Returns the pulse matrix

        Returns:
            np.ndarray: pulse matrix
        """


@dataclass
class IQPair:
    I: Waveform
    Q: Waveform
