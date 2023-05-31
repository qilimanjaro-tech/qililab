"""X gate"""
from qibo import gates

from qililab.pulse.hardware_gates.hardware_gate import HardwareGate
from qililab.pulse.hardware_gates.hardware_gate_factory import HardwareGateFactory
from qililab.typings import GateName


@HardwareGateFactory.register
class X(HardwareGate):  # pylint: disable=invalid-name
    """X gate."""

    name = GateName.X
    class_type = gates.X

    @classmethod
    def translate(cls, gate: gates.X) -> HardwareGate.HardwareGateSettings:
        """Translate gate into pulse.

        Returns:
            tuple[float, float]: Amplitude and phase of the pulse.
        """
        qubit = gate.target_qubits[0]
        return cls.settings[qubit]
