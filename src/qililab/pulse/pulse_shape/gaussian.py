"""Gaussian pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName


@dataclass(frozen=True, eq=True)
class Gaussian(PulseShape):
    """Gaussian pulse shape"""

    name = PulseShapeName.GAUSSIAN
    num_sigmas: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """Gaussian envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        return (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Gaussian":
        """Load Gaussian object/shape from dictionary.

        Args:
            dictionary (dict): Dictionary representation of the Gaussian object.

        Returns:
            Gaussian: Loaded class.
        """
        num_sigmas = dictionary[PulseShapeSettingsName.NUM_SIGMAS.value]
        return cls(num_sigmas=num_sigmas)

    def to_dict(self):
        """Return dictionary representation of the Gaussian shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.NUM_SIGMAS.value: self.num_sigmas,
        }
