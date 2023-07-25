"""Drag gate"""
import numpy as np

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.transpiler import Drag as Drag_gate
from qililab.typings import GateName


@HardwareGateFactory.register
class Drag(HardwareGate):
    """Drag pulse gate.

    This is a gate representation of the Drag pulse as a native gate.
    """

    name = GateName.Drag
    class_type = Drag_gate

    @classmethod
    def translate(cls, gate: Drag_gate, gate_schedule: list[dict]) -> list[dict]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        gate_schedule = gate_schedule[0]

        theta = cls.normalize_angle(angle=gate.parameters[0])
        amplitude = gate_schedule.amplitude * theta / np.pi
        phase = cls.normalize_angle(angle=gate.parameters[1])

        gate_schedule.amplitude = amplitude
        gate_schedule.phase = phase

        return [gate_schedule]
