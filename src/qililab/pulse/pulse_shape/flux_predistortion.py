"""Flux predistortion pulse shape."""
from dataclasses import dataclass, field

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(eq=True, frozen=True)
class FluxPredistortion(PulseShape):
    """Exponential decay correction (loop) pulse shape."""

    name = PulseShapeName.FLUX_PREDISTORTION
    coef : np.ndarray
    sampling_rate: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Distorted flux pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        
        ysig = amplitude * np.ones(round(duration / resolution))

        ycorr = signal.lfilter([1], self.coef, ysig)
        norm = np.amax(np.abs(ycorr)) 
        ycorr = ycorr/norm
        
        # import matplotlib.pyplot as plt
        # plt.plot(ycorr)
        # plt.show()
        
        return ycorr

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.COEF.value: self.coef,
        }

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.coef), self.sampling_rate))
    
    def __eq__(self, other):
        return self.name == other.name and all(self.coef == other.coef) and self.sampling_rate == other.sampling_rate