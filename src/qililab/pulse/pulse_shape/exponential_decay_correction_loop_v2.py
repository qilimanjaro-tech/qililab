"""Exponential decay correction (loop) pulse shape (version 2)."""
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
class ExponentialCorrectionLoopV2(PulseShape):
    """Exponential decay correction (loop) pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION_LOOP_V2
    tau_exponential1: float
    tau_exponential2: float
    amp1: float
    amp2: float
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

        # Predistortion 1
        a0 = 1
        a1 = (self.tau_exponential1*(1+2*self.amp1)-1)/(2*self.tau_exponential1*(1+self.amp1)+1)

        b0 = (2*self.tau_exponential1+1)/(2*self.tau_exponential1+(1+self.amp1)+1)
        b1 = (-2*self.tau_exponential1+1)/(2*self.tau_exponential1*(1+self.amp1+1))

        a = [a0, a1]
        b = [b0, b1]

        ysig = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ysig)) 
        ysig = ysig/norm



        # Predistortion2
        alpha = 1 - np.exp(-1/(self.sampling_rate*self.tau_exponential2*(1+self.amp2)))

        if self.amp2 >= 0.0:
            k = self.amp2/(1+self.amp2-alpha)
            b = [(1-k + k*alpha), -(1-k)*(1-alpha)]
        else:
            k = -self.amp2/(1+self.amp2)/(1-alpha)
            b = [(1+k - k*alpha), -(1-k)*(1-alpha)]

        a = [1, -(1-alpha)]

        ysig = signal.lfilter(b, a, ysig)
        norm = np.amax(np.abs(ysig)) 
        ysig = ysig/norm

        return ysig

    def to_dict(self):
        """Return dictionary representation of the pulse shape.
        
        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.TAU_EXPONENTIAL1.value: self.tau_exponential1,
            PulseShapeSettingsName.TAU_EXPONENTIAL2.value: self.tau_exponential2,
            PulseShapeSettingsName.AMP1.value: self.amp1,
            PulseShapeSettingsName.AMP2.value: self.amp2,
        }