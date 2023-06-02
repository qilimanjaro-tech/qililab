"""PulsedGates class. Contains the gates that can be directly translated into a pulse."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from qibo.gates import Gate

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
    class_type: type[Gate]
    settings: dict[int | tuple[int, int], HardwareGateSettings]  # qubit -> HardwareGateSettings

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

        Args:
            gate (Gate): Gate to be translated.

        Returns:
            HardwareGateSettings: Amplitude and phase of the pulse.
        """
