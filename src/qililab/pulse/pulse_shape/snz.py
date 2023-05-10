"""SNZ pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class SNZ(PulseShape):
    """Sudden net zero pulse shape. See supplementary material I in https://arxiv.org/abs/2008.07411"""

    name = PulseShapeName.SNZ
    b: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Constant amplitude envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse
            resolution (float): Pulse resolution

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        envelope = np.zeros(round(duration / resolution))
        phi_t = 3  # total time between halfpulses, this is always 3
        halfpulse_t = np.ceil(
            (duration - phi_t) / 2
        )  # TODO: is it  a problem if we lose some time due to int division?

        envelope[: halfpulse_t / resolution] = amplitude * np.ones(
            round(halfpulse_t / resolution)
        )  # positive square halfpulse
        envelope[halfpulse_t / resolution] = self.b
        envelope[halfpulse_t / resolution + 1] = 0
        envelope[halfpulse_t / resolution + 2] = -self.b
        envelope[halfpulse_t / resolution + 3 :] = -amplitude * np.ones(round(halfpulse_t / resolution))

        return envelope

    @classmethod
    def from_dict(cls, dictionary: dict) -> "SNZ":
        """Load SNZ object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the SNZ object/shape.

        Returns:
            Rectangular: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary representation of the Rectangular object/shape.

        Returns:
            dict: Dictionary.
        """
        # TODO uncomment method once #294 is merged
        raise NotImplementedError("Method to be implemented soon")
        # return {
        #     RUNCARD.NAME: self.name.value,
        #     PulseShapeSettingsName.B.value: self.b,
        # }
