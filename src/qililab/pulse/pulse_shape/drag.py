"""Drag pulse shape."""
from dataclasses import dataclass

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass(frozen=True, eq=True)
class Drag(PulseShape):
    """Derivative Removal by Adiabatic Gate (DRAG) pulse shape."""

    name = PulseShapeName.DRAG
    num_sigmas: float
    drag_coefficient: float

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """DRAG envelope centered with respect to the pulse.

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
        gaussian = (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
        return gaussian + 1j * self.drag_coefficient * (-(time - mu_) / sigma**2) * gaussian

    @classmethod
    def from_dict(cls, dictionary: dict) -> "Drag":
        """Load Drag object/shape from dictionary.
        Args:
            dictionary (dict): Dictionary representation of the Drag object/shape.
        Returns:
            Drag: Loaded class.
        """
        num_sigmas = dictionary[PulseShapeSettingsName.NUM_SIGMAS.value]
        drag_coefficient = dictionary[PulseShapeSettingsName.DRAG_COEFFICIENT.value]
        return cls(num_sigmas=num_sigmas, drag_coefficient=drag_coefficient)

    def to_dict(self):
        """Return dictionary representation of the Drag object/shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.NUM_SIGMAS.value: self.num_sigmas,
            PulseShapeSettingsName.DRAG_COEFFICIENT.value: self.drag_coefficient,
        }
