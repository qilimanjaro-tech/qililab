"""Drag pulse shape."""
from dataclasses import dataclass
from typing import Literal

import numpy as np

from qililab.constants import RUNCARD
from qililab.pulse.pulse_shape.pulse_shape import PulseShape
from qililab.typings import PulseShapeName
from qililab.typings.enums import MasterPulseShapeSettingsName, PulseShapeSettingsName
from qililab.utils import Factory


@Factory.register
@dataclass
class Drag(PulseShape):
    """Derivative Removal by Adiabatic Gate (DRAG) pulse shape."""

    name = PulseShapeName.DRAG
    num_sigmas: float
    drag_coefficient: float | Literal[MasterPulseShapeSettingsName.DRAG_COEFFICIENT]
    master_drag_coefficient: float | None = None

    def __post_init__(self):
        """Update drag coefficient value"""
        if (
            isinstance(self.drag_coefficient, str)
            and self.drag_coefficient != MasterPulseShapeSettingsName.DRAG_COEFFICIENT.value
        ):
            raise ValueError(
                f"master drag coefficient {self.drag_coefficient} does not have a valid value: {MasterPulseShapeSettingsName.DRAG_COEFFICIENT.value}."
            )
        if (
            isinstance(self.drag_coefficient, MasterPulseShapeSettingsName)
            and self.drag_coefficient != MasterPulseShapeSettingsName.DRAG_COEFFICIENT
        ):
            raise ValueError(
                f"master drag coefficient {self.drag_coefficient} does not have a valid value: {MasterPulseShapeSettingsName.DRAG_COEFFICIENT.value}."
            )
        if isinstance(self.drag_coefficient, str):
            self.drag_coefficient = MasterPulseShapeSettingsName.DRAG_COEFFICIENT
        if (
            self.drag_coefficient == MasterPulseShapeSettingsName.DRAG_COEFFICIENT
            and self.master_drag_coefficient is None
        ):
            raise ValueError(
                f"master drag coefficient pulse shape is not defined when drag coefficient value is {self.drag_coefficient}."
            )

    def _get_drag_coefficient(self) -> float:
        """Returns the associated drag coefficient value checking whether it has to retrieve
        it from the `master_drag coefficient_pulse_shape`"""
        if (
            self.drag_coefficient == MasterPulseShapeSettingsName.DRAG_COEFFICIENT
            and self.master_drag_coefficient is None
        ):
            raise ValueError(
                f"master drag coefficient pulse shape is not defined when drag coefficient value is {self.drag_coefficient}."
            )
        if self.drag_coefficient == MasterPulseShapeSettingsName.DRAG_COEFFICIENT:
            return self.master_drag_coefficient  # type: ignore
        if not isinstance(self.drag_coefficient, float):
            raise ValueError(f"Beta value type should be float. Got {type(self.drag_coefficient)} instead")
        return self.drag_coefficient

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """DRAG envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        drag_coefficient = self._get_drag_coefficient()
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        gaussian = (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
        return gaussian + 1j * drag_coefficient * (-(time - mu_) / sigma**2) * gaussian

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.NUM_SIGMAS.value: self.num_sigmas,
            PulseShapeSettingsName.DRAG_COEFFICIENT.value: self.drag_coefficient
            if isinstance(self.drag_coefficient, float)
            else self.drag_coefficient.value,
            MasterPulseShapeSettingsName.DRAG_COEFFICIENT.value: self.master_drag_coefficient
            if self.master_drag_coefficient is not None
            else None,
        }
