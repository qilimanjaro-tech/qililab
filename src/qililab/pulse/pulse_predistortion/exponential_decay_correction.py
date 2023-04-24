"""Exponential decay correction pulse shape with both v1 and v2 together"""
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
@dataclass(unsafe_hash=True, frozen=True, eq=True)
class ExponentialCorrection(PulseShape):
    """Exponential decay correction pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION
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

        if self.amp >= 0.0:
            
            # Parameters
            alpha = 1 - np.exp(-1/(self.sampling_rate*self.tau_exponential*(1+self.amp)))

            k = self.amp/(1+self.amp-alpha)
            b = [(1-k + k*alpha), -(1-k)*(1-alpha)]

            a = [1, -(1-alpha)]    
            
        # TODO: Check if there should be another if here, or just a else.
        elif self.amp < 0.0:
            
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