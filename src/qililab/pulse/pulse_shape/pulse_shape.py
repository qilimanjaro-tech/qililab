"""PulseShape abstract base class."""
from abc import ABC, abstractmethod

import numpy as np


class PulseShape(ABC):
    """Pulse shape abstract base class."""

    name: str

    @abstractmethod
    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0) -> np.ndarray:
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
