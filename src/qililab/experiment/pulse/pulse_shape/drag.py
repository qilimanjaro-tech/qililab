"""Drag pulse shape."""
import numpy as np

from qililab.experiment.pulse.pulse_shape.pulse_shape import PulseShape


class Drag(PulseShape):
    """Derivative Removal by Adiabatic Gate (DRAG) pulse shape."""

    def __init__(self, name: str, sigma: float, beta: float):
        super().__init__(name=name)
        self.sigma = sigma
        self.beta = beta

    def envelope(self, duration: int, amplitude: float):
        """DRAG envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        time = np.arange(duration)
        mu_ = duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / self.sigma**2)
        return gaussian + 1j * self.beta * (-(time - mu_) / self.sigma**2) * gaussian
