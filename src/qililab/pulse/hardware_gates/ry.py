"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.y import Y
from qililab.settings.gate_settings import CircuitPulseSettings
from qililab.typings import GateName


@HardwareGateFactory.register
class RY(HardwareGate):
    """RY gate."""

    name = GateName.RY
    class_type = gates.RY

    @classmethod
    def translate(cls, gate: gates.RY, gate_schedule: list[CircuitPulseSettings]) -> list[CircuitPulseSettings]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        if len(gate_schedule) > 1:
            raise ValueError(
                f"Schedule for gate {gate.name} is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
            )

        ry_schedule = gate_schedule[0]
        theta = gate.parameters[0]
        theta = cls.normalize_angle(angle=theta)
        ry_schedule.amplitude = (np.abs(theta) / np.pi) * ry_schedule.amplitude
        return [ry_schedule]
