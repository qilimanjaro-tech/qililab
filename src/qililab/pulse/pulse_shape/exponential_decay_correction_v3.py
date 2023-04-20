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
@dataclass(unsafe_hash=True, frozen=True, eq=True)
class ExponentialCorrectionV3(PulseShape):
    """Exponential decay correction pulse shape."""

    name = PulseShapeName.EXPONENTIAL_CORRECTION_V3
    tau_exponential: float
    amp: float
    b: float
    sampling_rate: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted square envelope.
        
        Corrects an exponential decay using a linear IIR filter.
        Fitting should be done to y = amp*exp(-t/tau)+B
        
        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.
            
        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        ysig = amplitude * np.ones(round(duration / resolution))

        # Parameters
        a0 = 1
        a1 = self.b/(self.tau_exponential*(self.amp+self.b))

        b0 = 1/(self.amp+self.b)
        b1 = 1/(self.tau_exponential*(self.amp+self.b))

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
            PulseShapeSettingsName.AMP.value: self.amp,
            PulseShapeSettingsName.B.value: self.b
        }