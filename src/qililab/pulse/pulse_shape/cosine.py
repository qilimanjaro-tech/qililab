"""Rectangular pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class Cosine(PulseShape):
    """Cosine pulse shape like A/2*(1-lambda_1*cos(phi)-lambda_2*cos(2phi)), giving a modified sinusoidal-gaussian.

        - lambda_1 cosine A/2*(1-cos(x)): Starts at height 0 (phase=0), maximum height A (phase=pi)
            and ends at height 0 (phase=2pi). Which is a sinusoidal like gaussian. Shaped like: _/\_

        - lambda_2 cosine A/2*(1-cos(2x)): Starts at height 0 (phase=0), maximum height A (phase=pi/2)
            then another height 0 in the middle at phase=pi, then another maximum height A (phase=3/2pi)
            and ends at height 0 (phase=2pi). Shaped like: _/v\_

    Total would be a sum of lambda_1 x _/\_ + lambda_2 _/v\_, giving a modified sinusoidal-gaussian.

    For more info check:
    - Supplemental material B. "Flux pulse parametrization" at [https://arxiv.org/abs/1903.02492],
    - OPTIMAL SOLUTION: SMALL CHANGE IN θ at [https://arxiv.org/abs/1402.5467]

    Atributes:
    lambda_2 (float): Parameter for moving the function A/2*(1-cos(x)) into A/2*(1-lambda_1*cos(x)-lambda_2*cos(2x))
                    which fulfills the constrain: 1=lambda_1+lambda_2.
    """

    name = PulseShapeName.COSINE
    lambda_2: float = 0.0  # between 0 and 1

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Modified sinusoidal-gaussian envelope.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        x_values = np.linspace(start=0, stop=2 * np.pi, num=int(duration / resolution))
        return amplitude / 2 * (1 - (1 - self.lambda_2) * np.cos(x_values) - self.lambda_2 * np.cos(2 * x_values))

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Cosine":
        """Load Cosine object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Cosine object/shape.

        Returns:
            Cosine: Loaded class.
        """
        local_dictionary = dictionary.copy()
        local_dictionary.pop(RUNCARD.NAME, None)
        return cls(**local_dictionary)

    def to_dict(self):
        """Return dictionary representation of the Cosine object/shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.LAMBDA_2.value: self.lambda_2,
        }
