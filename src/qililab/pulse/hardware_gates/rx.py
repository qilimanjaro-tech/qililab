"""RX gate"""
import numpy as np
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.pulse.hardware_gates.x import X
from qililab.settings.gate_settings import CircuitPulseSettings
from qililab.typings import GateName


@HardwareGateFactory.register
class RX(HardwareGate):
    """RX gate."""

    name = GateName.RX
    class_type = gates.RX

    @classmethod
    def translate(cls, gate: gates.RX, gate_schedule: list[CircuitPulseSettings]) -> list[CircuitPulseSettings]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        if len(gate_schedule) > 1:
            raise ValueError(
                f"Schedule for gate {gate.name} is expected to have only 1 pulse but instead found {len(gate_schedule)} pulses"
            )

        rx_schedule = gate_schedule[0]
        theta = gate.parameters[0]
        theta = cls.normalize_angle(angle=theta)
        rx_schedule.amplitude = (np.abs(theta) / np.pi) * rx_schedule.amplitude
        return [rx_schedule]
