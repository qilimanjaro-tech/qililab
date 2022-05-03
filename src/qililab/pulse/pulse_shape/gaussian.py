"""Gaussian pulse shape."""
import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape


class Gaussian(PulseShape):
    """Gaussian pulse shape"""

    def __init__(self, name: str, sigma: float):
        super().__init__(name=name)
        self.sigma = sigma

    def envelope(self, duration: int, amplitude: float):
        """Gaussian envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        time = np.arange(duration)
        mu_ = duration / 2
        return amplitude * np.exp(-0.5 * (time - mu_) ** 2 / self.sigma**2)
