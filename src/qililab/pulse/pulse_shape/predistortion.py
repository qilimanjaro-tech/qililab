"""Predistortion pulse shape (bias tee + filter)."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(unsafe_hash=True, frozen=True, eq=True)
class Predistortion(PulseShape):
    """Predistortion pulse shape (bias tee + filter)."""

    name = PulseShapeName.PREDISTORTION
    tau_bias_tee: float
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

        #Bias tee correction
        k1 = 2 * self.tau_bias_tee*self.sampling_rate
        a1 = [1, -1]
        b1 = [(k1 + 1) / k1, -(k1 - 1) / k1]

        ysig = signal.lfilter(b1, a1, ysig)
        norm = np.amax(np.abs(ysig))
        ysig = ysig/norm

        # Exponential correction
        alpha = 1 - np.exp(-1/(self.sampling_rate*self.tau_exponential*(1+self.amp)))

        if self.amp >= 0.0:
            k2 = self.amp/(1+self.amp-alpha)
            b2 = [(1-k2 + k2*alpha), -(1-k2)*(1-alpha)]
        else:
            k2 = -self.amp/(1+self.amp)/(1-alpha)
            b2 = [(1+k2 - k2*alpha), -(1-k2)*(1-alpha)]

        a2 = [1, -(1-alpha)]

        ysig = signal.lfilter(b2, a2, ysig)
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
            PulseShapeSettingsName.TAU_BIAS_TEE.value: self.tau_bias_tee,
            PulseShapeSettingsName.TAU_EXPONENTIAL.value: self.tau_exponential,
            PulseShapeSettingsName.AMP.value: self.amp,
        }