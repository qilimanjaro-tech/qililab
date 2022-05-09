"""Gaussian pulse shape."""
import numpy as np

from qililab.pulse.pulse_shape.pulse_shape import PulseShape


class Gaussian(PulseShape):
    """Gaussian pulse shape"""

    name = "Gaussian"

    def __init__(self, num_sigmas: float):
        self.num_sigmas = num_sigmas

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Gaussian envelope centered with respect to the pulse.

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
        return (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
