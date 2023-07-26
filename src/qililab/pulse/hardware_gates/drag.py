"""Drag gate"""
import numpy as np

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.settings.gate_settings import CircuitPulseSettings
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
    def translate(cls, gate: Drag_gate, gate_schedule: list[CircuitPulseSettings]) -> list[CircuitPulseSettings]:
        """Translate gate into pulse.

        Returns:
            Tuple[float, float]: Amplitude and phase of the pulse.
        """
        if len(gate_schedule) > 1:
            raise ValueError(
                f"Schedule for the drag gate is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
            )

        drag_schedule = gate_schedule[0]

        theta = cls.normalize_angle(angle=gate.parameters[0])
        amplitude = drag_schedule.amplitude * theta / np.pi
        phase = cls.normalize_angle(angle=gate.parameters[1])

        drag_schedule.amplitude = amplitude
        drag_schedule.phase = phase

        return [drag_schedule]
