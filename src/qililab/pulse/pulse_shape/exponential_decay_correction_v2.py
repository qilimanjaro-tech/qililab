"""Exponential decay correction pulse shape (version 2). It is better for shorter pulses but it has a problem with amplitudes."""
from dataclasses import dataclass

import numpy as np
from scipy import signal 
import matplotlib.pyplot as plt

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(unsafe_hash=True, eq=True)
class ExponentialCorrectionV2(PulseShape):
    """Exponential decay correction pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION_V2
    tau_exponential: float
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
        a0 = 1
        a1 = (self.tau_exponential*(1+2*self.amp)-1)/(2*self.tau_exponential*(1+self.amp)+1)

        b0 = (2*self.tau_exponential+1)/(2*self.tau_exponential+(1+self.amp)+1)
        b1 = (-2*self.tau_exponential+1)/(2*self.tau_exponential*(1+self.amp+1))

        a = [a0, a1]
        b = [b0, b1]


        # Filtered signal
        ycorr = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ycorr)) 
        ycorr = (1/norm)*ycorr

        plt.plot(ycorr)

        return ycorr

    def to_dict(self):
        """Return dictionary representation of the pulse shape.
        
        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU_EXPONENTIAL.value: self.tau_exponential,
            PulseShapeSettingsName.AMP.value: self.amp
        }