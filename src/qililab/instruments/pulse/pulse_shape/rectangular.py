"""Rectangular pulse shape."""
import numpy as np

from qililab.instruments.pulse.pulse_shape.pulse_shape import PulseShape


class Rectangular(PulseShape):
    """Rectangular/square pulse shape."""

    def __init__(self, name: str):
        super().__init__(name=name)

    def envelope(self, duration: int, amplitude: float):
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        return amplitude * np.ones(duration)
