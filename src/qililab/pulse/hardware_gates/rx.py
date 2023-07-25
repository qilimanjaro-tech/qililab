"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.x import X
from qililab.typings import GateName


@HardwareGateFactory.register
class RX(HardwareGate):
    """RX gate."""

    name = GateName.RX
    class_type = gates.RX

    @classmethod
    def translate(cls, gate: gates.RX, gate_schedule: list[dict]) -> list[dict]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """

        gate_schedule = gate_schedule[0]
        theta = gate.parameters[0]
        theta = cls.normalize_angle(angle=theta)
        gate_schedule.amplitude = (np.abs(theta) / np.pi) * gate_schedule.amplitude
        return [gate_schedule]
