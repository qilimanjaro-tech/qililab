"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.y import Y
from qililab.typings import GateName


@HardwareGateFactory.register
class RY(HardwareGate):
    """RY gate."""

    name = GateName.RY
    class_type = gates.RY

    @classmethod
    def translate(cls, gate: gates.RY, gate_schedule: list[dict]) -> list[dict]:

        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        
        gate_schedule = gate_schedule[0]
        qubit = gate.target_qubits[0]
        theta = gate.parameters[0]
        theta = cls.normalize_angle(angle=theta)
        gate_schedule.amplitude = (np.abs(theta) / np.pi) * gate_schedule.amplitude
        return [gate_schedule]