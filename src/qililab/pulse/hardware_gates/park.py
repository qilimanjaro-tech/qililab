"""Parking gate"""
from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.transpiler import Park as Park_gate
from qililab.typings import GateName


# TODO: park gate no longer needed, but is left here to not break current experiments
@HardwareGateFactory.register
class Park(HardwareGate):  # pylint: disable=invalid-name
    """Park gate."""

    name = GateName.Park
    class_type = Park_gate

    @classmethod
    def translate(cls, gate: Park_gate, gate_schedule: list[dict]) -> list[dict]:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        return gate_schedule
