"""PulseShape abstract base class."""
from abc import ABC, abstractmethod


class PulseShape(ABC):
    """Pulse shape abstract base class."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def envelope(self, duration: int, amplitude: int):
        """Compute the amplitudes of the pulse shape envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
