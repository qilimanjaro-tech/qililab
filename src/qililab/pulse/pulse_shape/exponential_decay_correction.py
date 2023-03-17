"""Exponential decay correction pulse shape."""
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
class ExponentialCorrection(PulseShape):
    """Exponential decay correction pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION
    tau: float
    amp: float
    sampling_rate: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted square envelope.

        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = g*(1+amp*exp(-t/tau)), where g is ignored in the corrections.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        ysig = amplitude * np.ones(round(duration / resolution))
        
        # Parameters
        alpha = 1 - np.exp(1/(self.sampling_rate*self.tau*(1+self.amp)))

        if self.amp >= 0.0:
            k = self.amp/(1+self.amp-alpha)
        else:
            k = self.amp/((1+self.amp)*(1-alpha))
        
        b = [(1-k + k*alpha), -(1+k)*(1-alpha)]
        a = [1, -(1-alpha)]

        # Filtered signal
        ycorr = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ycorr)) 
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
            PulseShapeSettingsName.AMP.value: self.amp
        }
