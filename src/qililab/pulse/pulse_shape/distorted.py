"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(unsafe_hash=True, eq=True)
class Distorted(PulseShape):
    """Distorted/square pulse shape."""

    name: PulseShapeName = PulseShapeName.DISTORTED

    def envelope(self, duration: int, amplitude: float, tau: float, resolution: float = 1.0):
        """Distorted square envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        ysig = amplitude * np.ones(round(duration / resolution))
        k = 2 * tau
        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]

        return signal.lfilter(b, a, ysig)
