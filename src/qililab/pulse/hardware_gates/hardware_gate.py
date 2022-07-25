"""PulsedGates class. Contains the gates that can be directly translated into a pulse."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Type

import numpy as np
from qibo.abstractions.gates import Gate

from qililab.typings import GateName
from qililab.typings.enums import MasterGateSettingsName
from qililab.utils import SingletonABC


def _use_master_value_when_variable_is_referencing_master_name(
    gate_current_value: int | float | MasterGateSettingsName, master_amplitude_gate: float, master_duration_gate: int
):  # sourcery skip: remove-unnecessary-cast
    """use master value when variable is referencing master name"""
    if not isinstance(gate_current_value, MasterGateSettingsName):
        return gate_current_value
    if gate_current_value not in [
        MasterGateSettingsName.MASTER_AMPLITUDE_GATE,
        MasterGateSettingsName.MASTER_DURATION_GATE,
    ]:
        raise ValueError(
            f"Master Name {gate_current_value} not supported. The only supported names are: "
            + f"[{MasterGateSettingsName.MASTER_AMPLITUDE_GATE}, {MasterGateSettingsName.MASTER_DURATION_GATE}]"
        )
    if gate_current_value == MasterGateSettingsName.MASTER_AMPLITUDE_GATE:
        return float(master_amplitude_gate)
    return int(master_duration_gate)


class HardwareGate(ABC, metaclass=SingletonABC):
    """Settings of a specific pulsed gate."""

    @dataclass
    class HardwareGateSettings:
        """HardwareGate settings."""

        amplitude: float | Literal[MasterGateSettingsName.MASTER_AMPLITUDE_GATE]
        phase: float
        duration: int | Literal[MasterGateSettingsName.MASTER_DURATION_GATE]
        shape: dict

    name: GateName
    class_type: Type[Gate]
    settings: HardwareGateSettings | None = None

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
    def translate(cls, gate: Gate, master_amplitude_gate: float, master_duration_gate: int) -> HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """

    @classmethod
    def parameters(cls, master_amplitude_gate: float, master_duration_gate: int) -> HardwareGateSettings:
        """Return the gate parameters.

        Raises:
            ValueError: If no parameters are specified.

        Returns:
            HardwareGateSettings: Gate parameters.
        """
        if cls.settings is None:
            raise ValueError(f"Please specify the parameters of the {cls.name.value} gate.")

        return cls._apply_master_values_to_hardware_gate_settings(
            settings=cls.settings,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )

    @classmethod
    def _apply_master_values_to_hardware_gate_settings(
        cls, settings: HardwareGateSettings, master_amplitude_gate: float, master_duration_gate: int
    ):
        """Apply master values to Hardware Gate Settings when
        settings values refer to master settings parameters
        """
        settings.amplitude = _use_master_value_when_variable_is_referencing_master_name(
            gate_current_value=settings.amplitude,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
        settings.duration = _use_master_value_when_variable_is_referencing_master_name(
            gate_current_value=settings.duration,
            master_amplitude_gate=master_amplitude_gate,
            master_duration_gate=master_duration_gate,
        )
        return settings
