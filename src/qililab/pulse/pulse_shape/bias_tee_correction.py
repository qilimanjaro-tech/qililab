"""Bias tee correction pulse shape."""
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
class BiasTeeCorrection(PulseShape):
    """Bias tee correction pulse shape."""

    name = PulseShapeName.BIAS_TEE_CORRECTION
    tau: float
    sampling_rate: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted square envelope.

        Corrects for a bias tee using a linear IIR filter with time connstant tau.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        ysig = amplitude * np.ones(round(duration / resolution))
        
        k = 2 * self.tau*self.sampling_rate
        a = [1, -1]
        b = [(k + 1) / k, -(k - 1) / k]
        
        ycorr = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ycorr))
        #norm = a[0]**(duration / resolution) * b[0]**(duration / resolution) 
        ycorr = ycorr/norm

        return ycorr

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU.value: self.tau,
        }
