"""CZ gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class CZ(HardwareGate):  # pylint: disable=invalid-name
    """CZ gate.

    CZ / C-Phase gate (2 qubit gate)
    Sends a Sudden Net Zero (SNZ) pulse to the target in CZ(control, target)
    If no t_phi is defined, allows for other standard pulse shapes
    """

    name = GateName.CZ
    class_type = gates.CZ

    @classmethod
    def translate(cls, gate: gates.CZ, gate_schedule: list[dict]) -> list[dict]:
        """Translate gate into pulse.
        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        return gate_schedule
