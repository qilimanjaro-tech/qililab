"""Flux predistortion pulse shape."""
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

        ycorr = signal.lfilter(self.coef, 1, ysig)
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
            PulseShapeSettingsName.COEF.value: self.coef,
        }
