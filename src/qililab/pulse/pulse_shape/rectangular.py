"""Rectangular pulse shape."""
import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
class Rectangular(PulseShape):
    """Rectangular/square pulse shape."""

    name = PulseShapeName.RECTANGULAR

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        return amplitude * np.ones(round(duration / resolution))
