"""LFilterRectangular pulse shape."""
from dataclasses import dataclass

import numpy as np
from scipy import signal

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName, PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class LFilterRectangular(PulseShape):
    """LFilterRectangular pulse shape."""

    name = PulseShapeName.LFILTER_RECTANGULAR
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
        corr_envelope = corr_envelope * norm / corr_norm * self.norm_factor

        return corr_envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> "LFilterRectangular":
        """Load LFilterRectangular object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the LFilterRectangular object/shape.

        Returns:
            LFilterRectangular: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary representation of the LFilterRectangular object/shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.NORM_FACTOR.value: self.norm_factor,
            PulseShapeSettingsName.A.value: self.a,
            PulseShapeSettingsName.B.value: self.b,
        }
