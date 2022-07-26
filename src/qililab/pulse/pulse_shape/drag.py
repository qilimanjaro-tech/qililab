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
    beta: float | Literal[MasterPulseShapeSettingsName.BETA]
    master_beta_pulse_shape: float | None = None

    def __post_init__(self):
        """Update beta value"""
        if isinstance(self.beta, str) and self.beta != MasterPulseShapeSettingsName.BETA.value:
            raise ValueError(
                f"master beta {self.beta} does not have a valid value: {MasterPulseShapeSettingsName.BETA.value}."
            )
        if isinstance(self.beta, MasterPulseShapeSettingsName) and self.beta != MasterPulseShapeSettingsName.BETA:
            raise ValueError(
                f"master beta {self.beta} does not have a valid value: {MasterPulseShapeSettingsName.BETA.value}."
            )
        if isinstance(self.beta, str):
            self.beta = MasterPulseShapeSettingsName.BETA
        if self.beta == MasterPulseShapeSettingsName.BETA and self.master_beta_pulse_shape is None:
            raise ValueError(f"master beta pulse shape is not defined when beta value is {self.beta}.")

    def _get_beta(self) -> float:
        """Returns the associated beta value checking whether it has to retrieve
        it from the `master_beta_pulse_shape`"""
        if self.beta == MasterPulseShapeSettingsName.BETA and self.master_beta_pulse_shape is None:
            raise ValueError(f"master beta pulse shape is not defined when beta value is {self.beta}.")
        if self.beta == MasterPulseShapeSettingsName.BETA:
            return self.master_beta_pulse_shape  # type: ignore
        if not isinstance(self.beta, float):
            raise ValueError(f"Beta value type should be float. Got {type(self.beta)} instead")
        return self.beta

    def envelope(self, duration: int, amplitude: float, resolution: float = 1.0):
        """DRAG envelope centered with respect to the pulse.

        Args:
            duration (int): Duration of the pulse (ns).
            amplitude (float): Maximum amplitude of the pulse.

        Returns:
            ndarray: Amplitude of the envelope for each time step.
        """

        beta = self._get_beta()
        sigma = duration / self.num_sigmas
        time = np.arange(duration / resolution) * resolution
        mu_ = duration / 2
        gaussian = amplitude * np.exp(-0.5 * (time - mu_) ** 2 / sigma**2)
        gaussian = (gaussian - gaussian[0]) / (1 - gaussian[0])  # Shift to avoid introducing noise at time 0
        return gaussian + 1j * beta * (-(time - mu_) / sigma**2) * gaussian

    def to_dict(self):
        """Return dictionary representation of the pulse shape.

        Returns:
            dict: Dictionary.
        """
        return {
            RUNCARD.NAME: self.name.value,
            PulseShapeSettingsName.NUM_SIGMAS.value: self.num_sigmas,
            PulseShapeSettingsName.BETA.value: self.beta,
            MasterPulseShapeSettingsName.BETA.value: self.master_beta_pulse_shape
            if self.master_beta_pulse_shape is not None
            else None,
        }
