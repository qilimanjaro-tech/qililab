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

    def __repr__(self):
        """Return string representation of the PulseShape object."""
        return f"{self.name}"

    def __eq__(self, other: object) -> bool:
        """Compare PulseShape with another object.

        Args:
            other (object): PulseShape object.
        """
        return isinstance(other, Rectangular)
