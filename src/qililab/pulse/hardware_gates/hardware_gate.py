"""PulsedGates class. Contains the gates that can be directly translated into a pulse."""
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from qibo.gates import Gate

from qililab.typings import GateName
from qililab.utils import SingletonABC


class HardwareGate(ABC, metaclass=SingletonABC):
    """Settings of a specific pulsed gate."""

    name: GateName
    class_type: type[Gate]

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
    def translate(
        cls, gate: Gate, gate_schedule: list[dict]
    ) -> list[dict]:  # TODO: if we go for this implementation, maybe create a GateSchedule class
        """Translate gate into pulse.

        Args:
            gate (Gate): Gate to be translated.

        Returns:
            HardwareGateSettings: Amplitude and phase of the pulse.
        """
