"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(unsafe_hash=True, eq=True)
class Distorted(PulseShape):
    """Distorted/square pulse shape."""

    name = PulseShapeName.DISTORTED
    tau: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted square envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        ysig = amplitude * np.ones(round(duration / resolution))
        k = 2 * self.tau
        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]
        
        test = signal.lfilter(b, a, ysig)/(a[0]**(duration / resolution) * b[0]**(duration / resolution)+0.1)

        print(b[0]**(duration / resolution))
        return signal.lfilter(b, a, ysig)/(a[0]**(duration / resolution) * b[0]**(duration / resolution)+0.1)

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU.value: self.tau,
        }
