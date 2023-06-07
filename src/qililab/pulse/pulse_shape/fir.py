"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class LFilter(PulseShape):
    name = PulseShapeName.LFILTER
    a: list[float]
    b: list[float]
    norm_factor: float = 1.0

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        envelope = amplitude * np.ones(round(duration / resolution))
        norm = np.amax(np.real(envelope))
        corr_envelope = signal.lfilter(b=self.b, a=self.a, x=envelope)
        corr_norm = np.max(np.real(corr_envelope))
        corr_envelope = corr_envelope * (norm / corr_norm ) * self.norm_factor

        return corr_envelope
    
    
    def __hash__(self) -> int:
        return hash((self.name, tuple(self.a), tuple(self.b)))
    
    def __eq__(self, other):
        return self.name == other.name and all(self.a == other.a) and all(self.b == other.b) 
