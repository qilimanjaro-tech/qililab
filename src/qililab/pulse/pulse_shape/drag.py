"""Drag pulse shape."""
import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
class Drag(PulseShape):
    """Derivative Removal by Adiabatic Gate (DRAG) pulse shape."""

    name = PulseShapeName.DRAG

    def __init__(self, num_sigmas: float, beta: float):
        self.num_sigmas = num_sigmas
        self.beta = beta

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """DRAG envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        gaussian = (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
        return gaussian + 1j * self.beta * (-(time - mu_) / sigma**2) * gaussian

    def __repr__(self):
        """Return string representation of the PulseShape object."""
        return f"{self.name.value}(num_sigmas={self.num_sigmas}, beta={self.beta})"

    def __eq__(self, other: object) -> bool:
        """Compare PulseShape with another object.

        Args:
            other (object): PulseShape object.
        """
        return self.num_sigmas == other.num_sigmas and self.beta == other.beta if isinstance(other, Drag) else False
