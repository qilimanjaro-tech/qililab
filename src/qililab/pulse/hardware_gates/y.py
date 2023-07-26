"""Y gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.settings.gate_settings import CircuitPulseSettings
from qililab.typings import GateName


@HardwareGateFactory.register
class Y(HardwareGate):  # pylint: disable=invalid-name
    """Y gate."""

    name = GateName.Y
    class_type = gates.Y

    @classmethod
    def translate(cls, gate: gates.Y, gate_schedule: list[CircuitPulseSettings]) -> list[CircuitPulseSettings]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        return gate_schedule
