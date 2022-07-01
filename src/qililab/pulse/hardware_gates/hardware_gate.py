"""PulsedGates class. Contains the gates that can be directly translated into a pulse."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Type

import numpy as np
from qibo.abstractions.gates import Gate

from qililab.typings import GateName
from qililab.utils import SingletonABC


class HardwareGate(ABC, metaclass=SingletonABC):
    """Settings of a specific pulsed gate."""

    @dataclass
    class HardwareGateSettings:
        """HardwareGate settings."""

        amplitude: float
        phase: float
        duration: int
        shape: dict

    name: GateName
    class_type: Type[Gate]
    settings: HardwareGateSettings | None = None

    def __init__(self, settings: dict):
        class_type = type(self)
        class_type.settings = self.HardwareGateSettings(**settings)

    @classmethod
    def normalize_angle(cls, angle: float):
        """Normalize angle in range [-pi, pi].

        Args:
            angle (float): Normalized angle.
        """
        angle %= 2 * np.pi
        if angle > np.pi:
            angle -= 2 * np.pi
        return angle

    @classmethod
    @abstractmethod
    def translate(cls, gate: Gate) -> HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """

    @classmethod
    def parameters(cls) -> HardwareGateSettings:
        """Return the gate parameters.

        Raises:
            ValueError: If no parameters are specified.

        Returns:
            HardwareGateSettings: Gate parameters.
        """
        if cls.settings is None:
            raise ValueError(f"Please specify the parameters of the {cls.name.value} gate.")
        return cls.settings
